"""Retriever over the chunk index with three modes:

- dense:  cosine similarity of Gemini embeddings (default)
- bm25:   keyword scoring
- hybrid: both rankings combined with Reciprocal Rank Fusion (RRF)

backend/eval/evaluate.py compares them on a labelled question set."""

import json
from functools import lru_cache

import numpy as np

from backend.rag import config
from backend.rag.gemini_client import embed_texts
from backend.rag.ingestion.chunking import searchable_text
from backend.rag.retrieval.bm25 import BM25, tokenize


MODES = ("hybrid", "dense", "bm25")


def reciprocal_rank_fusion(rankings, k=config.RRF_K):
    """Fuse ranked lists of chunk indices (best first) into {index: score}.

    Each list contributes 1 / (k + rank), so a chunk ranked well by both
    retrievers beats one ranked first by only one of them.
    """
    fused = {}

    for ranking in rankings:
        for rank, index in enumerate(ranking, start=1):
            fused[index] = fused.get(index, 0.0) + 1.0 / (k + rank)

    return fused


class Retriever:
    def __init__(self, chunks, embeddings, documents):
        self.chunks = chunks
        self.embeddings = embeddings
        self.documents = {document["file"]: document for document in documents}
        self.bm25 = BM25([tokenize(searchable_text(chunk)) for chunk in chunks])

    @classmethod
    def load(cls, index_path=config.INDEX_PATH, embeddings_path=config.EMBEDDINGS_PATH):
        if not index_path.exists() or not embeddings_path.exists():
            raise FileNotFoundError(
                "Retrieval index not found. Build it with: "
                "python -m backend.rag.ingestion.build_index"
            )

        index = json.loads(index_path.read_text(encoding="utf-8"))
        embeddings = np.load(embeddings_path)

        if index["embedding_model"] != config.EMBEDDING_MODEL:
            raise RuntimeError(
                f"Index was built with {index['embedding_model']} but the app "
                f"uses {config.EMBEDDING_MODEL}. Rebuild the index."
            )

        if len(index["chunks"]) != len(embeddings):
            raise RuntimeError("index.json and embeddings.npy are out of sync. Rebuild the index.")

        return cls(index["chunks"], embeddings, index["documents"])

    def search(self, query, top_k=config.TOP_K, mode=config.RETRIEVAL_MODE, query_embedding=None):
        """Return the top_k chunks for a query.

        mode: "dense", "bm25" or "hybrid" (see module docstring).
        query_embedding can be passed in to skip the embedding API call.
        """
        if mode not in MODES:
            raise ValueError(f"mode must be one of {MODES}")

        similarity = None

        if mode in ("hybrid", "dense"):
            if query_embedding is None:
                query_embedding = embed_texts([query], "RETRIEVAL_QUERY")[0]

            # Rows are normalised, so the dot product is cosine similarity
            similarity = self.embeddings @ query_embedding

        if mode == "dense":
            order = np.argsort(-similarity)[:top_k]
        else:
            keyword_scores = np.asarray(self.bm25.scores(tokenize(query)))
            keyword_ranking = [
                index
                for index in np.argsort(-keyword_scores)[:config.FUSION_CANDIDATES]
                if keyword_scores[index] > 0
            ]

            if mode == "bm25":
                order = keyword_ranking[:top_k]
            else:
                dense_ranking = np.argsort(-similarity)[:config.FUSION_CANDIDATES]
                fused = reciprocal_rank_fusion([dense_ranking, keyword_ranking])
                order = sorted(fused, key=fused.get, reverse=True)[:top_k]

        return [self._to_result(int(index), similarity) for index in order]

    def _to_result(self, index, similarity):
        chunk = self.chunks[index]
        document = self.documents[chunk["file"]]

        return {
            "chunk_id": chunk["id"],
            "file": chunk["file"],
            "title": document["short_title"],
            "page": chunk["page"],
            "section": chunk.get("section"),
            "text": chunk["text"],
            "similarity": None if similarity is None else round(float(similarity[index]), 4),
        }

    def stats(self):
        return {
            "documents": [
                {
                    "title": document["short_title"],
                    "pages": document["pages"],
                    "chunks": document["chunks"],
                }
                for document in self.documents.values()
            ],
            "chunks": len(self.chunks),
        }


@lru_cache(maxsize=1)
def get_retriever():
    return Retriever.load()
