import os
from dotenv import load_dotenv

from qdrant_client import QdrantClient

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION = "bis_docs"


def inspect_document(doc_id):

    print("\n" + "=" * 80)
    print(f"DOCUMENT: {doc_id}")
    print("=" * 80)

    all_points = []
    offset = None

    # Read all points without filtering
    while True:

        points, offset = client.scroll(
            collection_name=COLLECTION,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False
        )

        all_points.extend(points)

        if offset is None:
            break

    # Keep only the requested document
    points = [
        p for p in all_points
        if p.payload.get("doc_id") == doc_id
    ]

    # Sort by page
    points.sort(
        key=lambda p: (
            p.payload.get("page", 9999),
            str(p.payload.get("clause", ""))
        )
    )

    print(f"Found {len(points)} chunks.")

    for i, point in enumerate(points[:15], start=1):

        payload = point.payload

        print(f"\n--- Chunk {i} ---")
        print("Page   :", payload.get("page"))
        print("Clause :", payload.get("clause"))
        print("Title  :", payload.get("doc_title"))

        print("Text:")
        print(payload.get("text", "")[:800])


inspect_document("IS 17526:2021")
inspect_document("IS 17803")
