import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

EMBEDDINGS_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "embeddings.json"
)

MODEL_NAME = "all-MiniLM-L6-v2"


# ---------------------------------------------------------
# LOAD EMBEDDINGS
# ---------------------------------------------------------

print("Loading embeddings...")
print(f"Embeddings path: {EMBEDDINGS_PATH}")

if not EMBEDDINGS_PATH.exists():
    raise FileNotFoundError(
        f"Embeddings file not found: {EMBEDDINGS_PATH}"
    )

with open(EMBEDDINGS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total embeddings: {len(data)}")


# ---------------------------------------------------------
# LOAD EMBEDDING MODEL
# ---------------------------------------------------------

print("Loading embedding model...")

model = SentenceTransformer(MODEL_NAME)

print("Embedding model loaded successfully.")


# ---------------------------------------------------------
# RETRIEVAL FUNCTION
# ---------------------------------------------------------

def retrieve(query, top_k=5):

    query_embedding = model.encode(
        [query],
        normalize_embeddings=True
    )[0]

    scores = []

    for item in data:

        chunk_embedding = np.array(
            item["embedding"]
        )

        similarity = np.dot(
            query_embedding,
            chunk_embedding
        )

        scores.append({
            "score": float(similarity),
            "chunk_id": item["chunk_id"],
            "source": item["source"],
            "text": item["text"]
        })

    scores.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return scores[:top_k]


# ---------------------------------------------------------
# DIRECT TEST
# ---------------------------------------------------------

if __name__ == "__main__":

    query = input("\nEnter your question: ")

    results = retrieve(
        query,
        top_k=5
    )

    print("\n" + "=" * 80)
    print("TOP RESULTS")
    print("=" * 80)

    for i, result in enumerate(results, start=1):

        print(f"\n#{i}")
        print(f"Score: {result['score']:.4f}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Source: {result['source']}")
        print(f"Text:\n{result['text']}")

    print("\n" + "=" * 80)