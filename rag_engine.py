from retriever import retrieve
from generator import generate_answer


def ask(query: str, top_k: int = 5) -> dict:
    """
    Main RAG function.

    Input:
        query = user's question

    Output:
        answer
        confidence
        sources
    """

    chunks = retrieve(query, top_k=top_k)

    return generate_answer(query, chunks)


if __name__ == "__main__":

    test_queries = [
        "What is IS 17526 about?",
        "What are the requirements for stainless steel vacuum bottles?",
        "What is IS 17803 about?",
        "What is the purpose of BIS certification?",
        "What is the capital of France?"
    ]

    for q in test_queries:

        print("\n" + "=" * 60)
        print(f"Q: {q}")

        result = ask(q)

        print(f"Confidence: {result['confidence']}")

        print(f"Answer:\n{result['answer']}")

        print("Sources used:")

        for s in result["sources"]:
            print(
                f"  {s['standard_id']} | "
                f"Clause {s['clause']} | "
                f"Page {s['page']} | "
                f"Score {s['score']}"
            )
