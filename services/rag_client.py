import requests


RAG_API_URL = "http://192.168.1.10:8000/ask"


def ask_rag(query: str) -> dict:
    response = requests.post(
        RAG_API_URL,
        json={"query": query},
        timeout=60
    )

    response.raise_for_status()

    return response.json()