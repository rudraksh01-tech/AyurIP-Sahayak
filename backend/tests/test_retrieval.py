import numpy as np
import pytest

from backend.rag.retrieval.bm25 import BM25, tokenize
from backend.rag.retrieval.retriever import Retriever, reciprocal_rank_fusion


CHUNKS = [
    {"id": 0, "file": "a.pdf", "page": 1, "section": "10.2 Neem", "text": "The neem patent was revoked by the EPO."},
    {"id": 1, "file": "a.pdf", "page": 2, "section": "10.1 Turmeric", "text": "Turmeric was used to heal wounds."},
    {"id": 2, "file": "b.pdf", "page": 1, "section": None, "text": "Basmati rice is grown in India and Pakistan."},
]

DOCUMENTS = [
    {"file": "a.pdf", "short_title": "Doc A", "pages": 2, "chunks": 2},
    {"file": "b.pdf", "short_title": "Doc B", "pages": 1, "chunks": 1},
]


@pytest.fixture
def retriever():
    # One-hot embeddings: chunk i is the only perfect match for unit vector i
    return Retriever(CHUNKS, np.eye(3, dtype=np.float32), DOCUMENTS)


def test_tokenize_lowercases_and_drops_stopwords():
    assert tokenize("What is the TKDL, and how does it work?") == ["tkdl", "work"]


def test_bm25_ranks_matching_document_first():
    corpus = [tokenize(chunk["text"]) for chunk in CHUNKS]

    scores = BM25(corpus).scores(tokenize("neem patent"))

    assert scores[0] > 0
    assert scores[1] == scores[2] == 0


def test_reciprocal_rank_fusion_rewards_agreement():
    fused = reciprocal_rank_fusion([[1, 2], [2, 3]], k=60)

    assert max(fused, key=fused.get) == 2
    assert fused[1] == pytest.approx(1 / 61)


def test_dense_search_uses_query_embedding(retriever):
    results = retriever.search("anything", mode="dense", query_embedding=np.array([0, 1, 0], dtype=np.float32))

    assert results[0]["chunk_id"] == 1
    assert results[0]["similarity"] == pytest.approx(1.0)
    assert results[0]["title"] == "Doc A"
    assert results[0]["page"] == 2


def test_bm25_search_needs_no_embedding(retriever):
    results = retriever.search("basmati rice", mode="bm25")

    assert [result["chunk_id"] for result in results] == [2]
    assert results[0]["similarity"] is None


def test_hybrid_search_fuses_both_rankings(retriever):
    # Dense prefers chunk 1, keywords only match chunk 0: both appear, and
    # chunk 0 wins because it is also ranked by dense search.
    embedding = np.array([0.5, 0.9, 0.0], dtype=np.float32)

    results = retriever.search("neem patent", top_k=2, mode="hybrid", query_embedding=embedding)

    assert [result["chunk_id"] for result in results] == [0, 1]


def test_search_rejects_unknown_mode(retriever):
    with pytest.raises(ValueError):
        retriever.search("neem", mode="magic")


def test_stats_counts_documents_and_chunks(retriever):
    stats = retriever.stats()

    assert stats["chunks"] == 3
    assert [document["title"] for document in stats["documents"]] == ["Doc A", "Doc B"]


def test_load_explains_how_to_build_a_missing_index(tmp_path):
    with pytest.raises(FileNotFoundError, match="build_index"):
        Retriever.load(tmp_path / "index.json", tmp_path / "embeddings.npy")
