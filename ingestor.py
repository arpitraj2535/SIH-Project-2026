import os
import re
import uuid
import time
from typing import List, Dict

import fitz
import voyageai
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, StrictModeConfig

# ============================================================
# CONFIG
# ============================================================

load_dotenv()

MODEL_NAME = "voyage-4-lite"
COLLECTION = "bis_docs_voyage_final"
VECTOR_SIZE = 1024

# Keep the existing chunking unchanged.
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

# Your actual Voyage account limits:
# 10,000 TPM / 3 RPM.
# We deliberately stay below the TPM ceiling.
VOYAGE_SAFE_TOKENS = 7500
VOYAGE_MAX_TEXTS = 1000

# 61s keeps us safely under 3 requests/minute.
VOYAGE_SUCCESS_DELAY = 61

# A failed request may still count against the rate limit,
# so retries also wait before trying again.
VOYAGE_RETRY_DELAY = 65
VOYAGE_MAX_RETRIES = 4

# Small Qdrant writes reduce request-body/timeout risk.
QDRANT_BATCH_SIZE = 25
QDRANT_TIMEOUT = 300
QDRANT_MAX_RETRIES = 4
QDRANT_RETRY_DELAY = 10

# Qdrant writes use wait=False, then we explicitly verify IDs.
QDRANT_VERIFY_RETRIES = 8
QDRANT_VERIFY_DELAY = 5

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not VOYAGE_API_KEY:
    raise ValueError("VOYAGE_API_KEY not found in .env")
if not QDRANT_URL:
    raise ValueError("QDRANT_URL not found in .env")
if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY not found in .env")

# ============================================================
# CLIENTS
# ============================================================

print("Connecting to Voyage AI...")

# We control retries ourselves so the 3 RPM account limit is
# never accidentally bypassed by the SDK.
voyage_client = voyageai.Client(
    api_key=VOYAGE_API_KEY,
    max_retries=0,
    timeout=120,
)

print("Connected to Voyage AI.")

print("Connecting to Qdrant Cloud...")

# Large client-side timeout directly addresses the previous
# httpx WriteTimeout during Qdrant upsert.
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=QDRANT_TIMEOUT,
)

print("Connected to Qdrant Cloud.")

# ============================================================
# COLLECTION
# ============================================================


def create_collection():
    existing = [
        c.name for c in client.get_collections().collections
    ]

    if COLLECTION in existing:
        print(f"Collection '{COLLECTION}' already exists.")
        return

    # Try the requested strict-mode setting first.
    try:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
            strict_mode_config=StrictModeConfig(enabled=False),
        )
        print(
            f"Collection '{COLLECTION}' created "
            f"with {VECTOR_SIZE}-dimensional vectors."
        )
        print("Qdrant strict_mode: disabled.")
        return
    except Exception as exc:
        print(
            "Warning: Qdrant Cloud did not accept strict_mode "
            f"configuration: {exc}"
        )
        print("Creating collection with Cloud defaults instead.")

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )

    print(
        f"Collection '{COLLECTION}' created "
        f"with {VECTOR_SIZE}-dimensional vectors."
    )

# ============================================================
# PDF EXTRACTION
# ============================================================


def extract_pages(pdf_path: str):
    doc = fitz.open(pdf_path)
    pages = []

    for page_number, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if text:
            pages.append({
                "page_num": page_number,
                "text": text,
            })

    doc.close()
    return pages

# ============================================================
# CLAUSE DETECTION
# ============================================================


def detect_clause(text: str):
    match = re.match(
        r"^(\d+\.\d+(?:\.\d+)*)",
        text.strip(),
    )

    if match:
        return match.group(1)

    return "general"

# ============================================================
# CHUNKING
# ============================================================


def chunk_page(
    page_text: str,
    page_num: int,
    doc_id: str,
    doc_title: str,
    source_url: str,
):
    chunks = []

    pattern = r"(?=\b\d+\.\d+(?:\.\d+)*\s)"
    parts = re.split(pattern, page_text)

    for part in parts:
        part = part.strip()

        if len(part) < 60:
            continue

        clause = detect_clause(part)

        if len(part) <= CHUNK_SIZE:
            chunks.append({
                "text": part,
                "page": page_num,
                "clause": clause,
                "doc_id": doc_id,
                "doc_title": doc_title,
                "standard_id": doc_id,
                "source_url": source_url,
            })

        else:
            start = 0

            while start < len(part):
                end = start + CHUNK_SIZE
                sub = part[start:end].strip()

                if len(sub) >= 60:
                    chunks.append({
                        "text": sub,
                        "page": page_num,
                        "clause": clause,
                        "doc_id": doc_id,
                        "doc_title": doc_title,
                        "standard_id": doc_id,
                        "source_url": source_url,
                    })

                if end >= len(part):
                    break

                start = end - CHUNK_OVERLAP

    return chunks

# ============================================================
# DETERMINISTIC POINT ID
# ============================================================


def point_id_for_chunk(chunk: Dict) -> str:
    return str(
        uuid.uuid5(
            uuid.NAMESPACE_URL,
            (
                f"{chunk['doc_id']}|"
                f"{chunk['page']}|"
                f"{chunk['clause']}|"
                f"{chunk['text']}"
            ),
        )
    )

# ============================================================
# QDRANT EXISTENCE CHECK
# ============================================================


def existing_point_ids(point_ids: List[str]) -> set:
    found = set()

    for start in range(0, len(point_ids), 100):
        ids = point_ids[start:start + 100]

        for attempt in range(1, QDRANT_MAX_RETRIES + 2):
            try:
                records = client.retrieve(
                    collection_name=COLLECTION,
                    ids=ids,
                    with_payload=False,
                    with_vectors=False,
                    timeout=QDRANT_TIMEOUT,
                )

                found.update(str(record.id) for record in records)
                break

            except Exception as exc:
                if attempt > QDRANT_MAX_RETRIES:
                    raise RuntimeError(
                        "Qdrant existence check failed after retries."
                    ) from exc

                print(
                    f"   Qdrant check failed "
                    f"(attempt {attempt}/{QDRANT_MAX_RETRIES + 1}). "
                    f"Waiting {QDRANT_RETRY_DELAY}s..."
                )
                time.sleep(QDRANT_RETRY_DELAY)

    return found

# ============================================================
# VOYAGE BATCH BUILDER
# ============================================================


def build_voyage_batches(chunks):
    batches = []
    current = []
    current_tokens = 0

    for chunk in chunks:
        text = chunk["text"]

        token_count = voyage_client.count_tokens(
            [text],
            model=MODEL_NAME,
        )

        if token_count > VOYAGE_SAFE_TOKENS:
            raise ValueError(
                f"One chunk has {token_count} tokens, exceeding "
                f"the safe request target of {VOYAGE_SAFE_TOKENS}."
            )

        if (
            current
            and (
                current_tokens + token_count > VOYAGE_SAFE_TOKENS
                or len(current) >= VOYAGE_MAX_TEXTS
            )
        ):
            batches.append(current)
            current = []
            current_tokens = 0

        current.append(chunk)
        current_tokens += token_count

    if current:
        batches.append(current)

    return batches

# ============================================================
# VOYAGE EMBEDDING WITH CONTROLLED RETRIES
# ============================================================


def generate_embeddings(texts):
    if not texts:
        return []

    for attempt in range(1, VOYAGE_MAX_RETRIES + 2):
        try:
            token_count = voyage_client.count_tokens(
                texts,
                model=MODEL_NAME,
            )

            print(
                f"   Voyage request: {len(texts)} texts / "
                f"{token_count} tokens"
            )

            if token_count > VOYAGE_SAFE_TOKENS:
                raise RuntimeError(
                    f"Batch has {token_count} tokens; "
                    f"safe maximum is {VOYAGE_SAFE_TOKENS}."
                )

            result = voyage_client.embed(
                texts,
                model=MODEL_NAME,
                input_type="document",
            )

            if len(result.embeddings) != len(texts):
                raise RuntimeError(
                    "Voyage returned a different number of embeddings."
                )

            print(
                f"   ✅ Voyage returned "
                f"{len(result.embeddings)} embeddings"
            )

            print(
                f"   Waiting {VOYAGE_SUCCESS_DELAY}s "
                "before next Voyage request..."
            )
            time.sleep(VOYAGE_SUCCESS_DELAY)

            return result.embeddings

        except Exception as exc:
            if attempt > VOYAGE_MAX_RETRIES:
                raise RuntimeError(
                    f"Voyage failed after {VOYAGE_MAX_RETRIES} retries."
                ) from exc

            print(
                f"   ⚠️ Voyage failed "
                f"(attempt {attempt}/{VOYAGE_MAX_RETRIES + 1})"
            )
            print(f"   Reason: {exc}")
            print(
                f"   Waiting {VOYAGE_RETRY_DELAY}s before retry..."
            )
            time.sleep(VOYAGE_RETRY_DELAY)

    raise RuntimeError("Unreachable")

# ============================================================
# QDRANT UPLOAD + VERIFICATION
# ============================================================


def upload_and_verify(points):
    if not points:
        return

    for start in range(0, len(points), QDRANT_BATCH_SIZE):
        batch = points[start:start + QDRANT_BATCH_SIZE]

        ids = [str(point.id) for point in batch]

        for attempt in range(1, QDRANT_MAX_RETRIES + 2):
            try:
                print(
                    f"   Qdrant upload "
                    f"{start + 1}-{start + len(batch)}/{len(points)}"
                )

                # wait=False prevents the Python client from waiting
                # for optimization/visibility during the write.
                client.upsert(
                    collection_name=COLLECTION,
                    points=batch,
                    wait=False,
                    timeout=QDRANT_TIMEOUT,
                )

                break

            except Exception as exc:
                if attempt > QDRANT_MAX_RETRIES:
                    raise RuntimeError(
                        "Qdrant upload failed after retries."
                    ) from exc

                print(
                    f"   ⚠️ Qdrant upload failed "
                    f"(attempt {attempt}/{QDRANT_MAX_RETRIES + 1})"
                )
                print(f"   Reason: {exc}")
                print(
                    f"   Waiting {QDRANT_RETRY_DELAY}s before retry..."
                )
                time.sleep(QDRANT_RETRY_DELAY)

        # Explicitly verify that every point is visible.
        for verify_attempt in range(1, QDRANT_VERIFY_RETRIES + 1):
            found = existing_point_ids(ids)
            missing = set(ids) - found

            if not missing:
                print(
                    f"   ✅ Qdrant verified "
                    f"{len(ids)}/{len(ids)} points"
                )
                break

            if verify_attempt == QDRANT_VERIFY_RETRIES:
                raise RuntimeError(
                    "Qdrant upload was not fully verified. "
                    "Stopping safely before continuing."
                )

            print(
                f"   Qdrant visibility: "
                f"{len(found)}/{len(ids)}. "
                f"Waiting {QDRANT_VERIFY_DELAY}s..."
            )
            time.sleep(QDRANT_VERIFY_DELAY)

# ============================================================
# UPDATE EXISTING QDRANT PAYLOADS
# ============================================================


def update_existing_payloads(chunks):
    """Update metadata only; vectors/embeddings are untouched."""
    for start in range(0, len(chunks), 100):
        batch = chunks[start:start + 100]

        for attempt in range(1, QDRANT_MAX_RETRIES + 2):
            try:
                for chunk in batch:
                    client.set_payload(
                        collection_name=COLLECTION,
                        payload={
                            "source_url": chunk["source_url"],
                            "doc_id": chunk["doc_id"],
                            "doc_title": chunk["doc_title"],
                            "standard_id": chunk["standard_id"],
                            "page": chunk["page"],
                            "clause": chunk["clause"],
                        },
                        points=[point_id_for_chunk(chunk)],
                        wait=True,
                        timeout=QDRANT_TIMEOUT,
                    )

                print(
                    f"   Updated source metadata "
                    f"{start + 1}-{start + len(batch)}/{len(chunks)}"
                )
                break

            except Exception as exc:
                if attempt > QDRANT_MAX_RETRIES:
                    raise RuntimeError(
                        "Qdrant metadata update failed after retries."
                    ) from exc

                print(
                    f"   Qdrant metadata update failed "
                    f"(attempt {attempt}/{QDRANT_MAX_RETRIES + 1})"
                )
                print(f"   Reason: {exc}")
                time.sleep(QDRANT_RETRY_DELAY)


# ============================================================
# INGEST ONE PDF
# ============================================================


def ingest_pdf(
    pdf_path: str,
    doc_id: str,
    doc_title: str,
    source_url: str,
):
    print("\n" + "=" * 60)
    print(f"Processing: {pdf_path}")
    print(f"Document: {doc_title}")
    print("=" * 60)

    pages = extract_pages(pdf_path)

    chunks = []

    for page in pages:
        chunks.extend(
            chunk_page(
                page["text"],
                page["page_num"],
                doc_id,
                doc_title,
                source_url,
            )
        )

    print(f"   Extracted {len(chunks)} chunks")

    if not chunks:
        print("   No chunks found.")
        return 0

    # Check Qdrant BEFORE calling Voyage.
    point_ids = [
        point_id_for_chunk(chunk)
        for chunk in chunks
    ]

    found_ids = existing_point_ids(point_ids)

    # Update existing points with source URLs WITHOUT re-embedding.
    if found_ids:
        existing_chunks = [
            chunk
            for chunk, point_id in zip(chunks, point_ids)
            if point_id in found_ids
        ]

        print(
            f"   Updating metadata for "
            f"{len(existing_chunks)} existing Qdrant points..."
        )
        update_existing_payloads(existing_chunks)

    missing_chunks = [
        chunk
        for chunk, point_id in zip(chunks, point_ids)
        if point_id not in found_ids
    ]

    print(
        f"   Already verified in Qdrant: "
        f"{len(found_ids)}/{len(chunks)}"
    )
    print(
        f"   Need Voyage embeddings: "
        f"{len(missing_chunks)}"
    )

    if not missing_chunks:
        print(
            f"✅ {doc_title}: all chunks already verified."
        )
        return len(chunks)

    batches = build_voyage_batches(missing_chunks)

    print(
        f"   Voyage requests required: {len(batches)}"
    )

    processed = 0

    for batch_number, batch_chunks in enumerate(batches, start=1):
        print(
            f"\n   Voyage batch "
            f"{batch_number}/{len(batches)}"
        )

        texts = [chunk["text"] for chunk in batch_chunks]
        embeddings = generate_embeddings(texts)

        points = [
            PointStruct(
                id=point_id_for_chunk(chunk),
                vector=embedding,
                payload=chunk,
            )
            for chunk, embedding in zip(
                batch_chunks,
                embeddings,
            )
        ]

        upload_and_verify(points)

        processed += len(points)

        print(
            f"   ✅ Verified progress: "
            f"{processed}/{len(missing_chunks)} new chunks"
        )

    print(
        f"\n✅ {doc_title}: "
        f"{len(chunks)} total chunks verified in Qdrant"
    )

    return len(chunks)
