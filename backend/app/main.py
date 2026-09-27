import itertools
import json
import logging
import time
from collections import defaultdict, deque
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from google.genai import errors as genai_errors
from pydantic import BaseModel, Field, field_validator

from backend.rag import config
from backend.rag.gemini_client import GeminiConfigError
from backend.rag.rag_pipeline import ask_rag, stream_rag
from backend.rag.retrieval.retriever import get_retriever


logger = logging.getLogger("uvicorn.error")


app = FastAPI(
    title="AyurIP Sahayak API",
    description=(
        "Hybrid-retrieval RAG assistant for Ayurveda, Traditional Knowledge "
        "and Intellectual Property Rights."
    ),
    version="2.0.0",
)


# ---------------------------------------------------------
# RATE LIMITING
# ---------------------------------------------------------

class RateLimiter:
    """Sliding-window limit per client, kept in memory.

    Enough to stop one visitor from draining the Gemini free-tier quota of a
    public demo; each server instance keeps its own counts.
    """

    def __init__(self, limit, window_seconds=60):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)

    def allow(self, key):
        now = time.monotonic()
        timestamps = self.requests[key]

        while timestamps and now - timestamps[0] > self.window_seconds:
            timestamps.popleft()

        if len(timestamps) >= self.limit:
            return False

        timestamps.append(now)
        return True


rate_limiter = RateLimiter(config.RATE_LIMIT_PER_MINUTE)


def client_ip(request: Request):
    # Behind Vercel's proxy the real client is the first X-Forwarded-For entry
    forwarded = request.headers.get("x-forwarded-for", "")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknown"


# ---------------------------------------------------------
# SCHEMAS
# ---------------------------------------------------------

class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=4000)


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    history: list[ChatTurn] = Field(default_factory=list, max_length=12)

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, value):
        value = value.strip()

        if not value:
            raise ValueError("Question cannot be empty.")

        return value


# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "model": config.GENERATION_MODEL,
        **get_retriever().stats(),
    }


def describe_error(error):
    """Map a pipeline exception to (HTTP status, message safe to show users)."""
    if isinstance(error, GeminiConfigError):
        logger.error(str(error))
        return 503, "The server is missing its Gemini API key. Please contact the site owner."

    logger.exception("RAG pipeline failed", exc_info=error)

    if isinstance(error, genai_errors.APIError):
        if error.code == 429:
            return 429, "The AI service is busy (free-tier limit reached). Please try again in a minute."

        return 502, "The AI service returned an error. Please try again."

    return 500, "Sahayak could not generate an answer right now. Please try again."


def check_rate_limit(request: Request):
    if not rate_limiter.allow(client_ip(request)):
        raise HTTPException(
            status_code=429,
            detail="Too many questions in a short time. Please wait a minute and try again.",
        )


@app.post("/api/ask")
def ask_question(payload: QuestionRequest, request: Request):
    """Answer a question and return the full result as JSON."""
    check_rate_limit(request)

    history = [turn.model_dump() for turn in payload.history]

    try:
        result = ask_rag(payload.question, history)
    except Exception as error:
        status, message = describe_error(error)
        raise HTTPException(status_code=status, detail=message) from error

    return {
        "question": payload.question,
        **result,
    }


@app.post("/api/ask/stream")
def ask_question_stream(payload: QuestionRequest, request: Request):
    """Stream the answer as newline-delimited JSON events (see stream_rag)."""
    check_rate_limit(request)

    history = [turn.model_dump() for turn in payload.history]
    events = stream_rag(payload.question, history)

    # Run retrieval before the response starts, so failures there still get
    # a proper HTTP status instead of an error inside a 200 stream.
    try:
        first_event = next(events)
    except Exception as error:
        status, message = describe_error(error)
        raise HTTPException(status_code=status, detail=message) from error

    def ndjson():
        try:
            for event in itertools.chain([first_event], events):
                yield json.dumps(event, ensure_ascii=False) + "\n"
        except Exception as error:
            _, message = describe_error(error)
            yield json.dumps({"type": "error", "message": message}) + "\n"

    return StreamingResponse(
        ndjson(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------
# FRONTEND
# ---------------------------------------------------------

# Serve the built React app (frontend/dist) from the same origin. API routes
# always take priority. During development the Vite dev server is used instead.
if config.FRONTEND_DIST.is_dir():
    app.frontend("/", directory=config.FRONTEND_DIST)
