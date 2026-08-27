from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag.rag_pipeline import ask


app = FastAPI(
    title="AyurIP Sahayak API",
    description="AI-powered Ayurveda IP research assistant",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "message": "AyurIP Sahayak API is running!"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.post("/api/ask")
def ask_question(request: QuestionRequest):
    answer = ask(request.question)

    return {
        "question": request.question,
        "answer": answer,
    }
