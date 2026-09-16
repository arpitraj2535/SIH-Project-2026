import os
import fitz
import re
import uuid
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer


# CONFIG

load_dotenv()

MODEL_NAME = "BAAI/bge-small-en-v1.5"
COLLECTION = "bis_docs"

# ~375 tokens approximately
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200

BATCH_SIZE = 100


# MODELS / QDRANT


print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_URL:
    raise ValueError("QDRANT_URL not found in .env")

if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY not found in .env")

print("Connecting to Qdrant Cloud...")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

print("Connected to Qdrant Cloud.")


# COLLECTION


def create_collection():
    """
    Create the BIS document collection if it doesn't exist.
    """

    existing = [
        c.name
        for c in client.get_collections().collections
    ]

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


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pages(pdf_path: str):
    """
    Extract text page-by-page from a PDF.
    """

    doc = fitz.open(pdf_path)

    pages = []

    for page_number, page in enumerate(doc, start=1):

        text = page.get_text().strip()

        if text:
            pages.append({
                "page_num": page_number,
                "text": text
            })

    doc.close()

    return pages


# CLAUSE DETECTION


def detect_clause(text: str):
    """
    Detect clause numbers such as:
    4.1
    4.1.2
    7.15
    """

    match = re.match(
        r'^(\d+\.\d+(?:\.\d+)*)',
        text.strip()
    )

    if match:
        return match.group(1)

    return "general"


# CHUNKING


def chunk_page(
    page_text: str,
    page_num: int,
    doc_id: str,
    doc_title: str
):
    """
    Split page text into clause-aware chunks.

    Metadata stored with every chunk:
    - doc_id
    - doc_title
    - clause
    - page
    - text
    """

    chunks = []

    # Detect clause boundaries
    pattern = r'(?=\b\d+\.\d+(?:\.\d+)*\s)'

    parts = re.split(pattern, page_text)

    for part in parts:

        part = part.strip()

        if len(part) < 60:
            continue

        clause = detect_clause(part)

        # Small clause -> keep intact

        if len(part) <= CHUNK_SIZE:

            chunks.append({
                "text": part,
                "page": page_num,
                "clause": clause,
                "doc_id": doc_id,
                "doc_title": doc_title,
                "standard_id": doc_id
            })

        # Large clause -> overlapping chunks

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
                        "standard_id": doc_id
                    })

                if end >= len(part):
                    break

                start = end - CHUNK_OVERLAP

    return chunks


# BATCH UPLOAD


def upload_points(points):

    if not points:
        return

    for i in range(0, len(points), BATCH_SIZE):

        batch = points[i:i + BATCH_SIZE]

        client.upsert(
            collection_name=COLLECTION,
            points=batch
        )

        print(
            f"   Uploaded {min(i + BATCH_SIZE, len(points))}"
            f"/{len(points)} chunks"
        )


# INGEST ONE PDF


def ingest_pdf(
    pdf_path: str,
    doc_id: str,
    doc_title: str
):
    """
    Complete ingestion pipeline:

    PDF
      ↓
    Page extraction
      ↓
    Clause-aware chunking
      ↓
    BGE embeddings
      ↓
    Qdrant Cloud
    """

    print(f"\nProcessing: {pdf_path}")
    print(f"Document: {doc_title}")

    pages = extract_pages(pdf_path)

    points = []

    for page in pages:

        chunks = chunk_page(
            page["text"],
            page["page_num"],
            doc_id,
            doc_title
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

    print(f"   Generated {len(points)} chunks")

    upload_points(points)

    print(
        f"✅ {doc_title}: "
        f"{len(points)} chunks uploaded"
    )

    return len(points)
