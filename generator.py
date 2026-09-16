

import os
from groq import Groq
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY not found in .env")

client = Groq(api_key=GROQ_API_KEY)

MODEL_NAME = "openai/gpt-oss-120b"


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_context(chunks):

    context_parts = []

    for i, chunk in enumerate(chunks, start=1):

        context_parts.append(
            f"""
SOURCE {i}

Document: {chunk["doc_title"]}
Standard: {chunk["standard_id"]}
Clause: {chunk["clause"]}
Page: {chunk["page"]}

CONTENT:
{chunk["text"]}
"""
        )

    return "\n".join(context_parts)


# ============================================================
# DETERMINE CONFIDENCE
# ============================================================

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


# ============================================================
# GENERATE ANSWER
# ============================================================

def generate_answer(query, chunks):

    if not chunks:

        return {
            "answer": (
                "I don't have sufficient information in my verified "
                "BIS knowledge base to answer this question."
            ),
            "confidence": "red",
            "sources": []
        }

    context = build_context(chunks)

    prompt = f"""
You are an AI assistant for Indian Standards and BIS services.

Your job is to answer the user's question using ONLY the
VERIFIED BIS DOCUMENT CONTEXT provided below.

You are an evidence-grounded RAG assistant.

============================================================
STRICT EVIDENCE RULES
============================================================

1. Use ONLY information explicitly supported by the provided
   document context.

2. Do NOT use outside knowledge, even if you know the answer.

3. Do NOT invent facts, requirements, tests, standards,
   certifications, procedures, clause numbers, or page numbers.

4. NEVER strengthen a statement beyond what the source says.

   For example:

   Source says:
   "Copper, Stainless Steel, Aluminium"

   You may say:
   "The document lists copper, stainless steel and aluminium."

   Do NOT say:
   "These are the only materials permitted."

   unless the source explicitly says they are the only permitted
   materials.

5. Do NOT infer that something is mandatory unless the provided
   context explicitly establishes that it is mandatory.

6. Do NOT infer that something is prohibited unless the provided
   context explicitly establishes that it is prohibited.

7. Do NOT infer certification requirements from a general mention
   of BIS certification.

8. Do NOT combine information from different standards as though
   they belong to one standard.

9. If multiple standards appear in the context, keep their
   requirements clearly separated.

10. A requirement from Standard A must NEVER be presented as a
    requirement of Standard B.

11. If the user asks about a specific standard, prioritize evidence
    belonging to that standard.

12. If the context does not contain enough evidence to answer the
    question accurately, respond exactly:

    I don't have sufficient information in my verified BIS knowledge base to answer this question.

============================================================
CITATION RULES
============================================================

13. Every factual claim must have a citation.

14. Citations MUST use exactly this format:

    [StandardID, Clause X.X, Page Y]

15. If the source has no specific clause, use:

    [StandardID, Clause general, Page Y]

16. Use the StandardID, Clause and Page exactly as provided in the
    source metadata.

17. NEVER invent or modify a citation.

18. Do not cite a source merely because it is related to the topic.
    The source must actually support the claim being made.

19. When a statement contains information from two different
    sources, cite both sources.

============================================================
ANSWERING STYLE
============================================================

20. Answer the user's actual question directly.

21. Keep the answer concise.

22. Prefer bullet points for multiple requirements.

23. Do not add unnecessary background information.

24. Clearly distinguish between:

    - Product scope
    - Requirements
    - Testing
    - Sampling
    - Classification
    - Certification
    - Guidance
    - Labelling / marking

25. If the source only provides partial information, clearly state
    what the available document does and does not establish.

26. Do not pretend that a Product Manual contains the complete
    Indian Standard if the context only contains the Product Manual.

27. If a document says "refer to IS XXXXX", do not invent the
    contents of that referenced standard.

28. If the user asks a question outside the verified BIS knowledge
    base, use the exact insufficient-information response.

============================================================
VERIFIED BIS DOCUMENT CONTEXT
============================================================

{context}

============================================================
USER QUESTION
============================================================

{query}

============================================================
ANSWER
============================================================
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise, evidence-grounded BIS "
                    "standards assistant. Never go beyond the "
                    "provided evidence."
                )
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

    citations = [
        {
            "standard": chunk["standard_id"],
            "clause": chunk["clause"],
            "page": chunk["page"],
            "text": chunk["text"]
        }
        for chunk in chunks
    ]

    return {
        "answer": answer,
        "confidence": confidence,
        "sources": chunks,
        "citations": citations
    }


# ============================================================
# STANDALONE TEST
# ============================================================

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
