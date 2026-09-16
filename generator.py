# generator.py

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

client = Groq(api_key=GROQ_API_KEY)

MODEL_NAME = "openai/gpt-oss-120b"


# Build context from retrieved chunks


def build_context(chunks):

    context_parts = []

    for i, chunk in enumerate(chunks, start=1):

        context_parts.append(
            f"""
SOURCE {i}
Standard: {chunk["standard_id"]}
Clause: {chunk["clause"]}
Page: {chunk["page"]}

CONTENT:
{chunk["text"]}
"""
        )

    return "\n".join(context_parts)


# Determine confidence


def determine_confidence(chunks):

    if not chunks:
        return "red"

    top_score = chunks[0]["score"]

    if top_score >= 0.70:
        return "green"

    elif top_score >= 0.55:
        return "yellow"

    else:
        return "red"


# Generate answer


def generate_answer(query, chunks):

    if not chunks:
        return {
            "answer": "I don't have sufficient information in my verified BIS knowledge base to answer this question.",
            "confidence": "red",
            "sources": []
        }

    context = build_context(chunks)

    prompt = f"""
You are an AI assistant for Indian Standards and BIS services.

Your job is to answer questions ONLY using the provided BIS document context.

IMPORTANT RULES:

1. Do NOT use outside knowledge.
2. Do NOT invent facts.
3. Do NOT invent standards.
4. Do NOT invent clause numbers.
5. Do NOT invent page numbers.
6. Every factual claim must have a citation.
7. Citations MUST use this exact format:

[StandardID, Clause X.X, Page Y]

8. If a source has no specific clause, use:

[StandardID, Clause general, Page Y]

9. If the provided context does not contain enough information to answer the question, say exactly:

I don't have sufficient information in my verified BIS knowledge base to answer this question.

10. Keep the answer concise and useful.
11. Prefer bullet points when explaining multiple requirements.
12. Distinguish clearly between requirements, testing, classification, certification, and guidance.

VERIFIED BIS CONTEXT:

{context}

USER QUESTION:

{query}

ANSWER:
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are a precise BIS standards assistant. Follow the provided evidence strictly."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=1200
    )

    answer = response.choices[0].message.content

    confidence = determine_confidence(chunks)

    return {
        "answer": answer,
        "confidence": confidence,
        "sources": chunks
    }


# Standalone test

if __name__ == "__main__":

    print("Testing Groq connection...\n")

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": "Explain in one sentence what BIS is."
            }
        ],
        temperature=0.1,
        max_tokens=100
    )

    print(response.choices[0].message.content)
