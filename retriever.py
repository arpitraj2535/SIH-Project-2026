# retriever.py

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer


# Configuration


MODEL_NAME = "BAAI/bge-small-en-v1.5"
COLLECTION = "BIS"

TOP_K = 5
SCORE_THRESHOLD = 0.45


# Load embedding model


print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)


# Connect to Qdrant


client = QdrantClient(
    "localhost",
    port=6333
)


# Retrieve relevant chunks


def retrieve(query: str, top_k: int = TOP_K):

    # BGE models work better when queries use this prefix
    query_text = "Represent this sentence for searching relevant passages: " + query

    # Convert query into embedding
    query_embedding = model.encode(query_text).tolist()

    # Search Qdrant using the current API
    results = client.query_points(
        collection_name=COLLECTION,
        query=query_embedding,
        limit=top_k,
        with_payload=True,
        score_threshold=SCORE_THRESHOLD
    ).points

    retrieved_chunks = []

    for r in results:

        payload = r.payload

        retrieved_chunks.append({
            "text": payload.get("text", ""),
            "standard_id": payload.get("standard_id", "Unknown"),
            "page": payload.get("page", "Unknown"),
            "clause": payload.get("clause", "general"),
            "score": r.score
        })

    return retrieved_chunks


# Test retrieval

if __name__ == "__main__":

    test_query = "What are the requirements for stainless steel vacuum bottles?"

    print("\n" + "=" * 70)
    print("QUERY:")
    print(test_query)
    print("=" * 70)

    chunks = retrieve(test_query)

    if not chunks:
        print("\nNo relevant chunks found.")
    else:

        print(f"\nRetrieved {len(chunks)} relevant chunks:\n")

        for i, chunk in enumerate(chunks, start=1):

            print(f"--- Result {i} ---")

            print(f"Standard : {chunk['standard_id']}")
            print(f"Clause   : {chunk['clause']}")
            print(f"Page     : {chunk['page']}")
            print(f"Score    : {chunk['score']:.3f}")

            print("\nText:")
            print(chunk["text"][:1000])

            print("\n")
