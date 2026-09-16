import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

if not QDRANT_URL:
    raise ValueError("QDRANT_URL not found in .env")

if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY not found in .env")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

collections = client.get_collections()

print("\n✅ Connected to Qdrant Cloud!")
print("Collections:")

for collection in collections.collections:
    print("-", collection.name)
