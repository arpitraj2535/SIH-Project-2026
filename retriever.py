import os
import re
import time
import threading
from collections import deque

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter,
    FieldCondition,
    MatchValue
)
import voyageai


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

MODEL_NAME = "voyage-4-lite"
COLLECTION = "bis_docs_voyage_final"

TOP_K = 5
SCORE_THRESHOLD = 0.45

# Voyage account-specific free-tier limit:
# 3 requests per minute.
VOYAGE_MAX_REQUESTS = 3
VOYAGE_COOLDOWN = 65


# ============================================================
# VOYAGE RATE LIMITER
# ============================================================

_voyage_request_times = deque()
_voyage_lock = threading.Lock()
_voyage_cooldown_until = 0.0

HIGH_DEMAND_MESSAGE = (
    "\n⏳ High demand right now — our BIS knowledge engine is "
    "handling several requests. Please give us about a minute "
    "while we prepare your answer. Thank you for your patience! ❤️\n"
)


def wait_for_voyage_slot():
    """
    Enforce the current Voyage free-tier limit locally.

    After 3 successful embedding requests, wait 65 seconds before
    allowing another request. This prevents the application from
    repeatedly hitting Voyage's 3 RPM limit.
    """

    global _voyage_cooldown_until

    with _voyage_lock:

        now = time.monotonic()

        # If we are already in the post-3-request cooldown,
        # wait until the cooldown has finished.
        if now < _voyage_cooldown_until:
            wait_seconds = _voyage_cooldown_until - now

            print(HIGH_DEMAND_MESSAGE)
            print(
                f"Waiting {wait_seconds:.0f} seconds for "
                "the embedding service to become available..."
            )

            time.sleep(wait_seconds)

            now = time.monotonic()

        # Remove timestamps older than one minute.
        while (
            _voyage_request_times
            and now - _voyage_request_times[0] >= 60
        ):
            _voyage_request_times.popleft()

        # If 3 requests have been made inside the current
        # rolling minute, wait for the required cooldown.
        if len(_voyage_request_times) >= VOYAGE_MAX_REQUESTS:

            print(HIGH_DEMAND_MESSAGE)

            wait_seconds = VOYAGE_COOLDOWN

            print(
                f"Waiting {wait_seconds} seconds before "
                "sending the next query..."
            )

            time.sleep(wait_seconds)

            _voyage_request_times.clear()
            _voyage_cooldown_until = 0.0


def record_voyage_request():
    """
    Record a successful Voyage embedding request.

    Once three requests have completed, start a 65-second
    cooldown for the next request.
    """

    global _voyage_cooldown_until

    with _voyage_lock:

        _voyage_request_times.append(time.monotonic())

        if len(_voyage_request_times) >= VOYAGE_MAX_REQUESTS:
            _voyage_cooldown_until = (
                time.monotonic() + VOYAGE_COOLDOWN
            )


# ============================================================
# VOYAGE AI
# ============================================================

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")

if not VOYAGE_API_KEY:
    raise ValueError("VOYAGE_API_KEY not found in .env")

print("Connecting to Voyage AI...")

voyage_client = voyageai.Client(
    api_key=VOYAGE_API_KEY,
    max_retries=0,
    timeout=120
)

print("Connected to Voyage AI.")


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
    api_key=QDRANT_API_KEY,
    timeout=60
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
# VOYAGE QUERY EMBEDDING
# ============================================================

def embed_query(query: str):
    """
    Create a Voyage-4-lite query embedding while respecting
    the current 3-RPM account limit.
    """

    wait_for_voyage_slot()

    try:
        response = voyage_client.embed(
            [query],
            model=MODEL_NAME,
            input_type="query"
        )

    except Exception as exc:

        # If the provider still returns a rate-limit response
        # despite our local limiter, wait and retry once.
        if (
            "RateLimit" in type(exc).__name__
            or "rate limit" in str(exc).lower()
            or "3 RPM" in str(exc)
        ):

            print(HIGH_DEMAND_MESSAGE)
            print(
                f"Voyage rate limit reached. "
                f"Waiting {VOYAGE_COOLDOWN} seconds and retrying..."
            )

            time.sleep(VOYAGE_COOLDOWN)

            response = voyage_client.embed(
                [query],
                model=MODEL_NAME,
                input_type="query"
            )

        else:
            raise

    record_voyage_request()

    return response.embeddings[0]


# ============================================================
# RETRIEVE
# ============================================================

def retrieve(query: str, top_k: int = TOP_K):

    # --------------------------------------------------------
    # VOYAGE QUERY EMBEDDING
    # --------------------------------------------------------

    query_embedding = embed_query(query)

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
                        match=MatchValue(
                            value=document_ids[0]
                        )
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
            "source_url": payload.get("source_url", ""),
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

    # --------------------------------------------------------
    # RETURN TOP RESULTS
    # --------------------------------------------------------

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
