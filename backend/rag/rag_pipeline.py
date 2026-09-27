"""End-to-end RAG: question -> hybrid retrieval -> streamed Gemini answer with citations."""

import time

from backend.rag.generation.generator import find_citations, stream_answer
from backend.rag.retrieval.retriever import get_retriever


def build_search_query(question, history):
    """Short follow-ups ("what about neem?") don't say what they refer to,
    so search with the previous user question as well."""
    if not history or len(question.split()) >= 12:
        return question

    previous = next(
        (turn["content"] for turn in reversed(history) if turn["role"] == "user"),
        None,
    )

    return f"{previous}\n{question}" if previous else question


def _elapsed_ms(started):
    return round((time.perf_counter() - started) * 1000)


def stream_rag(question, history=None):
    """Yield events as the answer is produced:

    {"type": "sources", "sources": [...], "retrieval_ms": ...}  (first, after retrieval)
    {"type": "delta", "text": "..."}                            (many)
    {"type": "done", "cited": [1, 3], "generation_ms": ...}     (last)
    """
    history = history or []

    started = time.perf_counter()
    results = get_retriever().search(build_search_query(question, history))

    sources = [
        {**result, "number": number}
        for number, result in enumerate(results, start=1)
    ]

    yield {"type": "sources", "sources": sources, "retrieval_ms": _elapsed_ms(started)}

    started = time.perf_counter()
    parts = []

    for text in stream_answer(question, results, history):
        parts.append(text)
        yield {"type": "delta", "text": text}

    yield {
        "type": "done",
        "cited": sorted(find_citations("".join(parts), len(results))),
        "generation_ms": _elapsed_ms(started),
    }


def ask_rag(question, history=None):
    """Non-streaming wrapper around stream_rag() that returns the full result."""
    sources, parts, cited, timings = [], [], [], {}

    for event in stream_rag(question, history):
        if event["type"] == "sources":
            sources = event["sources"]
            timings["retrieval_ms"] = event["retrieval_ms"]
        elif event["type"] == "delta":
            parts.append(event["text"])
        elif event["type"] == "done":
            cited = event["cited"]
            timings["generation_ms"] = event["generation_ms"]

    return {
        "answer": "".join(parts),
        "sources": [
            {**source, "cited": source["number"] in cited}
            for source in sources
        ],
        "timings": timings,
    }


if __name__ == "__main__":

    query = input("\nAsk AyurIP-Sahayak: ")

    result = ask_rag(query)

    print("\n" + "=" * 80)
    print("FINAL ANSWER")
    print("=" * 80)
    print(result["answer"])

    print("\nSOURCES")
    print("=" * 80)

    for source in result["sources"]:
        marker = "*" if source["cited"] else " "
        print(
            f"{marker} [{source['number']}] {source['title']} | "
            f"page {source['page']} | {source['section']} | "
            f"similarity {source['similarity']}"
        )

    print("=" * 80)
    print(result["timings"])
