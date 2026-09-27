import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag.rag_pipeline import ask_rag


logger = logging.getLogger("uvicorn.error")


app = FastAPI(
    title="AyurIP Sahayak API",
    description="AI-powered Ayurveda IP research assistant",
    version="1.0.0",
)


# Allow the Vite dev server on any local port (localhost or 127.0.0.1)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
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
    try:
        result = ask_rag(request.question)
    except Exception as error:
        logger.exception("RAG pipeline failed")

        raise HTTPException(
            status_code=500,
            detail="Sahayak could not generate an answer right now. Please try again.",
        ) from error

    return {
        "question": request.question,
        "answer": result["answer"],
        "sources": result["sources"],
    }
