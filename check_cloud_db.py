import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION = "bis_docs"

info = client.get_collection(COLLECTION)

print("\n================================")
print("QDRANT CLOUD DATABASE")
print("================================")
print("Collection:", COLLECTION)
print("Points:", info.points_count)
print("Vectors:", info.indexed_vectors_count)
print("Status:", info.status)
