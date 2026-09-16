

import fitz
import re
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer


MODEL_NAME = "BAAI/bge-small-en-v1.5"
COLLECTION = "BIS"
CHUNK_SIZE = 600


# Load embedding model once
print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)

# Connect to Qdrant
client = QdrantClient("localhost", port=6333)


def create_collection():
    """
    Creates the Qdrant collection if it doesn't exist.
    """

    existing = [c.name for c in client.get_collections().collections]

    if COLLECTION in existing:
        print(f"Collection '{COLLECTION}' already exists.")
        return

    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )

    print(f"Collection '{COLLECTION}' created.")


def extract_pages(pdf_path: str):
    """
    Extract text from every page of a PDF.
    """

    doc = fitz.open(pdf_path)

    pages = []

    for i, page in enumerate(doc, start=1):

        text = page.get_text().strip()

        if text:
            pages.append({
                "page_num": i,
                "text": text
            })

    doc.close()

    return pages


def chunk_page(page_text: str, page_num: int, standard_id: str):
    """
    Split page text into clause-level chunks.

    Each chunk stores:
    - text
    - page
    - clause
    - standard_id
    """

    chunks = []

    # Detect clause numbers such as:
    # 4.1
    # 4.1.2
    # 7.15
    pattern = r'(?=\b\d+\.\d+[\.\d]*\s)'

    parts = re.split(pattern, page_text)

    for part in parts:

        part = part.strip()

        # Ignore tiny fragments
        if len(part) < 60:
            continue

        # Detect clause number
        clause_match = re.match(
            r'^(\d+\.\d+[\.\d]*)',
            part
        )

        clause = (
            clause_match.group(1)
            if clause_match
            else "general"
        )

        # Normal-sized chunk
        if len(part) <= CHUNK_SIZE:

            chunks.append({
                "text": part,
                "page": page_num,
                "clause": clause,
                "standard_id": standard_id
            })

        # Large clause → split into smaller chunks
        else:

            for i in range(0, len(part), CHUNK_SIZE):

                sub = part[i:i + CHUNK_SIZE].strip()

                if len(sub) < 60:
                    continue

                chunks.append({
                    "text": sub,
                    "page": page_num,
                    "clause": clause,
                    "standard_id": standard_id
                })

    return chunks


def ingest_pdf(pdf_path: str, standard_id: str):
    """
    Full ingestion pipeline:

    PDF
      ↓
    Page extraction
      ↓
    Clause chunks
      ↓
    Embeddings
      ↓
    Qdrant
    """

    print(f"\nProcessing: {pdf_path}")

    pages = extract_pages(pdf_path)

    points = []

    for page in pages:

        chunks = chunk_page(
            page["text"],
            page["page_num"],
            standard_id
        )

        for chunk in chunks:

            embedding = model.encode(
                chunk["text"]
            ).tolist()

            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload=chunk
                )
            )

    if points:

        client.upsert(
            collection_name=COLLECTION,
            points=points
        )

    print(
        f"✅ {standard_id}: "
        f"ingested {len(points)} chunks"
    )
