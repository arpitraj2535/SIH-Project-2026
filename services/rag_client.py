import os
import requests
from dotenv import load_dotenv

load_dotenv()

RAG_API_URL = os.getenv("RAG_API_URL")


def ask_rag(query: str) -> dict:
    response = requests.post(
        RAG_API_URL,
        json={"query": query},
        timeout=60
    )

    response.raise_for_status()

    return response.json()