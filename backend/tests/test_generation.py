from backend.rag import rag_pipeline
from backend.rag.generation import generator
from backend.rag.generation.generator import build_prompt, find_citations, stream_answer
from backend.rag.rag_pipeline import ask_rag, build_search_query, stream_rag


RESULTS = [
    {"chunk_id": 7, "file": "a.pdf", "title": "Doc A", "page": 11, "section": "3.5 TKDL", "text": "TKDL blocks patents.", "similarity": 0.8},
    {"chunk_id": 9, "file": "b.pdf", "title": "Doc B", "page": 3, "section": None, "text": "Neem was revoked.", "similarity": 0.6},
]


class FakeRetriever:
    def __init__(self):
        self.queries = []

    def search(self, query):
        self.queries.append(query)
        return RESULTS


def test_build_prompt_numbers_passages_with_location():
    prompt = build_prompt("What is TKDL?", RESULTS)

    assert "[1] Doc A, page 11 (3.5 TKDL)\nTKDL blocks patents." in prompt
    assert "[2] Doc B, page 3\nNeem was revoked." in prompt
    assert prompt.rstrip().endswith("QUESTION:\nWhat is TKDL?")
    assert "CONVERSATION SO FAR" not in prompt


def test_build_prompt_includes_recent_history():
    history = [
        {"role": "user", "content": "What is TKDL?"},
        {"role": "assistant", "content": "A digital library [1]."},
    ]

    prompt = build_prompt("Who created it?", RESULTS, history)

    assert "User: What is TKDL?\nAssistant: A digital library [1]." in prompt


def test_find_citations_ignores_out_of_range_numbers():
    answer = "TKDL helps [1][3]. Neem too [2, 7]. Also [10]."

    assert find_citations(answer, passage_count=6) == {1, 2, 3}


def test_stream_answer_without_results_skips_gemini(monkeypatch):
    monkeypatch.setattr(generator, "generate_stream", lambda *args: (_ for _ in ()).throw(AssertionError))

    assert "couldn't find" in "".join(stream_answer("anything", []))


def test_build_search_query_adds_previous_question_to_short_follow_ups():
    history = [
        {"role": "user", "content": "What happened in the turmeric patent case?"},
        {"role": "assistant", "content": "It was revoked."},
    ]

    assert build_search_query("And neem?", history) == "What happened in the turmeric patent case?\nAnd neem?"
    assert build_search_query("And neem?", []) == "And neem?"

    long_question = "Explain in detail how the European Patent Office handled the neem fungicide patent"
    assert build_search_query(long_question, history) == long_question


def test_stream_rag_yields_sources_then_deltas_then_citations(monkeypatch):
    retriever = FakeRetriever()
    monkeypatch.setattr(rag_pipeline, "get_retriever", lambda: retriever)
    monkeypatch.setattr(rag_pipeline, "stream_answer", lambda *args: iter(["TKDL ", "helps [1]."]))

    events = list(stream_rag("What is TKDL?"))

    assert [event["type"] for event in events] == ["sources", "delta", "delta", "done"]
    assert [source["number"] for source in events[0]["sources"]] == [1, 2]
    assert events[-1]["cited"] == [1]
    assert retriever.queries == ["What is TKDL?"]


def test_ask_rag_assembles_answer_and_marks_cited_sources(monkeypatch):
    monkeypatch.setattr(rag_pipeline, "get_retriever", FakeRetriever)
    monkeypatch.setattr(rag_pipeline, "stream_answer", lambda *args: iter(["Neem ", "was revoked [2]."]))

    result = ask_rag("What about neem?")

    assert result["answer"] == "Neem was revoked [2]."
    assert [source["cited"] for source in result["sources"]] == [False, True]
    assert set(result["timings"]) == {"retrieval_ms", "generation_ms"}
