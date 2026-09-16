import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION_NAME = "bis_docs"

existing = [c.name for c in client.get_collections().collections]

if COLLECTION_NAME in existing:
    print(f"Collection '{COLLECTION_NAME}' already exists.")
else:
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )
    print(f"✅ Collection '{COLLECTION_NAME}' created!")

print("\nCollections:")
for collection in client.get_collections().collections:
    print("-", collection.name)
