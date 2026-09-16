import os
import re

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue
)
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

MODEL_NAME = "BAAI/bge-small-en-v1.5"
COLLECTION = "bis_docs"

TOP_K = 5
SCORE_THRESHOLD = 0.45


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)


# ============================================================
# QDRANT CLOUD
# ============================================================

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


# ============================================================
# STANDARD DETECTION
# ============================================================

def detect_standard(query: str):
    """
    Detect an explicit IS number from the user's question.

    Examples:
        IS 17526
        IS 17526:2021
        IS 17803
    """

    match = re.search(
        r'\bIS\s*[-:]?\s*(\d{3,6})(?:\s*[:\-]\s*(\d{4}))?\b',
        query,
        re.IGNORECASE
    )

    if not match:
        return None

    number = match.group(1)
    year = match.group(2)

    return {
        "number": number,
        "year": year
    }


# ============================================================
# MAP STANDARD NUMBER TO STORED DOCUMENT ID
# ============================================================

STANDARD_MAP = {

    "17526": [
        "IS 17526:2021"
    ],

    "17803": [
        "IS 17803"
    ],

    "2925": [
        "IS-2925-Product-Manual"
    ],

    "4151": [
        "IS-4151-Product-Manual"
    ],

    "4250": [
        "approved-IS-4250-PM"
    ],

    "2347": [
        "PM-IS-2347"
    ],

    "4984": [
        "PM-IS-4984-June-2022"
    ],

    "4985": [
        "PM-IS-4985-Oct-2023"
    ],

    "694": [
        "PM_IS-694_March-2024"
    ],

    "1293": [
        "PM_1293-new-format-approved"
    ],

    "3854": [
        "PM_3854-approved"
    ],

    "1660": [
        "1660-PM-oct-2024"
    ],

    "2082": [
        "2082-PM_V6_-approved"
    ],

    "368": [
        "368-PM_10_July"
    ],
}


# ============================================================
# RETRIEVE
# ============================================================

def retrieve(query: str, top_k: int = TOP_K):

    # --------------------------------------------------------
    # BGE QUERY EMBEDDING
    # --------------------------------------------------------

    query_text = (
        "Represent this sentence for searching relevant passages: "
        + query
    )

    query_embedding = model.encode(
        query_text
    ).tolist()

    # --------------------------------------------------------
    # DETECT EXPLICIT STANDARD
    # --------------------------------------------------------

    detected = detect_standard(query)

    query_filter = None

    if detected:

        number = detected["number"]

        document_ids = STANDARD_MAP.get(number)

        if document_ids:

            # Use MUST because we currently have one exact
            # stored document ID for each standard.
            query_filter = Filter(
                must=[
                    FieldCondition(
                        key="standard_id",
                        match=MatchValue(value=document_ids[0])
                    )
                ]
            )

    # --------------------------------------------------------
    # DETECT "ABOUT / WHAT IS" QUESTION
    # --------------------------------------------------------

    about_question = bool(
        re.search(
            r'\b(what\s+is|what\s+does|about|describe|description|scope)\b',
            query,
            re.IGNORECASE
        )
    )

    # Retrieve more candidates for reranking
    search_limit = 20 if about_question else top_k

    # --------------------------------------------------------
    # QDRANT SEARCH
    # --------------------------------------------------------

    results = client.query_points(
        collection_name=COLLECTION,
        query=query_embedding,
        limit=search_limit,
        query_filter=query_filter,
        with_payload=True,
        score_threshold=SCORE_THRESHOLD
    ).points

    # --------------------------------------------------------
    # FORMAT + RERANK
    # --------------------------------------------------------

    candidates = []

    for r in results:

        payload = r.payload

        text = payload.get("text", "")
        page = payload.get("page", 999)
        clause = payload.get("clause", "general")
        score = r.score

        boosted_score = score

        if about_question:

            # Prefer introductory pages
            try:
                page_number = int(page)
            except (ValueError, TypeError):
                page_number = 999

            if page_number <= 3:
                boosted_score += 0.12

            # Prefer title/scope/product information
            intro_keywords = [
                "product manual",
                "product",
                "title",
                "scope",
                "this standard",
                "requirements"
            ]

            text_lower = text.lower()

            keyword_hits = sum(
                1
                for keyword in intro_keywords
                if keyword in text_lower
            )

            boosted_score += min(
                keyword_hits * 0.02,
                0.10
            )

            # Prefer general introductory chunks
            if clause == "general":
                boosted_score += 0.05

        candidates.append({
            "text": text,
            "standard_id": payload.get(
                "standard_id",
                "Unknown"
            ),
            "doc_id": payload.get(
                "doc_id",
                "Unknown"
            ),
            "doc_title": payload.get(
                "doc_title",
                "Unknown"
            ),
            "page": page,
            "clause": clause,
            "score": score,
            "_boosted_score": boosted_score
        })

    # --------------------------------------------------------
    # SORT BY RERANKED SCORE
    # --------------------------------------------------------

    candidates.sort(
        key=lambda x: x["_boosted_score"],
        reverse=True
    )

    retrieved_chunks = []

    for chunk in candidates[:top_k]:

        chunk.pop("_boosted_score", None)

        retrieved_chunks.append(chunk)

    return retrieved_chunks


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_queries = [

        "I manufacture stainless steel vacuum bottles. What BIS standard applies to my product?",

        "What are the capacity groups for domestic stainless steel vacuum flasks?",

        "I want to get BIS certification for my stainless steel vacuum flask. How many samples do I need to submit for testing"
    ]

    for test_query in test_queries:

        print("\n" + "=" * 70)
        print("QUERY:")
        print(test_query)
        print("=" * 70)

        chunks = retrieve(test_query)

        if not chunks:

            print("\nNo relevant chunks found.")

        else:

            print(
                f"\nRetrieved {len(chunks)} "
                "relevant chunks:\n"
            )

            for i, chunk in enumerate(
                chunks,
                start=1
            ):

                print(f"--- Result {i} ---")

                print(
                    f"Document : "
                    f"{chunk['doc_title']}"
                )

                print(
                    f"Standard : "
                    f"{chunk['standard_id']}"
                )

                print(
                    f"Clause   : "
                    f"{chunk['clause']}"
                )

                print(
                    f"Page     : "
                    f"{chunk['page']}"
                )

                print(
                    f"Score    : "
                    f"{chunk['score']:.3f}"
                )

                print("\nText:")
                print(
                    chunk["text"][:700]
                )

                print()
