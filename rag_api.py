from fastapi import FastAPI
from pydantic import BaseModel

from rag_engine import ask

app = FastAPI()


class Question(BaseModel):
    query: str


@app.post("/ask")
def ask_question(question: Question):

    result = ask(question.query)

    return result


@app.get("/")
def home():
    return {"status": "RAG API is running"}
