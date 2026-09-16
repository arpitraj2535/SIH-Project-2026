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
        "I manufacture stainless steel vacuum bottles. What BIS standard applies to my product?",
        "What are the capacity groups for domestic stainless steel vacuum flasks?",
        "I want to get BIS certification for my stainless steel vacuum flask. How many samples do I need to submit for testing?",
        "What materials can I use to make a metallic water bottle if I want it to comply with BIS requirements?",
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
