import json

import pytest
from fastapi.testclient import TestClient
from google.genai import errors as genai_errors

from backend.app import main
from backend.rag.gemini_client import GeminiConfigError


ANSWER = {
    "answer": "TKDL is a database [1].",
    "sources": [{"number": 1, "title": "Doc A", "page": 10, "cited": True}],
    "timings": {"retrieval_ms": 5, "generation_ms": 50},
}


class FakeRetriever:
    def stats(self):
        return {"documents": [{"title": "Doc A", "pages": 47, "chunks": 199}], "chunks": 199}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(main, "rate_limiter", main.RateLimiter(limit=100))
    monkeypatch.setattr(main, "get_retriever", FakeRetriever)
    monkeypatch.setattr(main, "ask_rag", lambda question, history: ANSWER)

    return TestClient(main.app, raise_server_exceptions=False)


def raise_error(error):
    def fail(*args, **kwargs):
        raise error

    return fail


def test_health_reports_knowledge_base(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["chunks"] == 199


def test_ask_returns_answer(client):
    response = client.post("/api/ask", json={"question": "  What is TKDL?  "})

    assert response.status_code == 200
    assert response.json()["question"] == "What is TKDL?"
    assert response.json()["answer"] == ANSWER["answer"]


@pytest.mark.parametrize("payload", [
    {"question": "   "},
    {"question": "x" * 501},
    {"question": "ok", "history": [{"role": "system", "content": "hi"}]},
])
def test_ask_rejects_invalid_input(client, payload):
    assert client.post("/api/ask", json=payload).status_code == 422


def test_ask_is_rate_limited_per_client(client, monkeypatch):
    monkeypatch.setattr(main, "rate_limiter", main.RateLimiter(limit=2))

    statuses = [client.post("/api/ask", json={"question": "TKDL?"}).status_code for _ in range(3)]

    assert statuses == [200, 200, 429]


@pytest.mark.parametrize("error, status", [
    (GeminiConfigError("no key"), 503),
    (genai_errors.APIError(429, {"error": {"message": "quota", "status": "RESOURCE_EXHAUSTED"}}), 429),
    (genai_errors.APIError(500, {"error": {"message": "boom", "status": "INTERNAL"}}), 502),
    (RuntimeError("bug"), 500),
])
def test_ask_maps_errors_to_friendly_statuses(client, monkeypatch, error, status):
    monkeypatch.setattr(main, "ask_rag", raise_error(error))

    response = client.post("/api/ask", json={"question": "TKDL?"})

    assert response.status_code == status
    assert "detail" in response.json()


def read_events(response):
    return [json.loads(line) for line in response.text.splitlines() if line]


def test_stream_sends_ndjson_events(client, monkeypatch):
    def fake_stream(question, history):
        yield {"type": "sources", "sources": [], "retrieval_ms": 1}
        yield {"type": "delta", "text": "Hello"}
        yield {"type": "done", "cited": [], "generation_ms": 2}

    monkeypatch.setattr(main, "stream_rag", fake_stream)

    response = client.post("/api/ask/stream", json={"question": "TKDL?"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/x-ndjson")
    assert [event["type"] for event in read_events(response)] == ["sources", "delta", "done"]


def test_stream_reports_retrieval_failure_as_http_error(client, monkeypatch):
    def fake_stream(question, history):
        raise GeminiConfigError("no key")
        yield

    monkeypatch.setattr(main, "stream_rag", fake_stream)

    assert client.post("/api/ask/stream", json={"question": "TKDL?"}).status_code == 503


def test_stream_reports_generation_failure_as_error_event(client, monkeypatch):
    def fake_stream(question, history):
        yield {"type": "sources", "sources": [], "retrieval_ms": 1}
        raise RuntimeError("stream broke")

    monkeypatch.setattr(main, "stream_rag", fake_stream)

    events = read_events(client.post("/api/ask/stream", json={"question": "TKDL?"}))

    assert events[-1]["type"] == "error"
    assert "try again" in events[-1]["message"]
