import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType


load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY")
)

COLLECTION = "bis_docs"


client.create_payload_index(
    collection_name=COLLECTION,
    field_name="standard_id",
    field_schema=PayloadSchemaType.KEYWORD
)

client.create_payload_index(
    collection_name=COLLECTION,
    field_name="doc_id",
    field_schema=PayloadSchemaType.KEYWORD
)


print("✅ Payload indexes created.")

info = client.get_collection(COLLECTION)

print("Collection:", COLLECTION)
print("Points:", info.points_count)
print("Status:", info.status)
