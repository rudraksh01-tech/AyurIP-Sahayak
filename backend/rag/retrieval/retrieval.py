import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np

EMBEDDINGS_PATH = Path("data/processed/embeddings.json")
MODEL_NAME = "all-MiniLM-L6-v2"

print("Loading embeddings...")

with open(EMBEDDINGS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total chunks loaded: {len(data)}")

print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)


def retrieve(query, top_k=5):

    print(f"\nQuery: {query}")

    query_embedding = model.encode(
        query,
        normalize_embeddings=True
    )

    embeddings = np.array([
        item["embedding"]
        for item in data
    ])

    similarities = embeddings @ query_embedding

    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []

    for rank, index in enumerate(top_indices, start=1):

        item = data[index]

        results.append({
            "rank": rank,
            "score": float(similarities[index]),
            "chunk_id": item["chunk_id"],
            "source": item["source"],
            "text": item["text"]
        })

    return results


if __name__ == "__main__":

    query = "What is Traditional Knowledge Digital Library (TKDL)?"

    results = retrieve(query, top_k=5)

    print("\n" + "=" * 60)
    print("TOP RETRIEVED CHUNKS")
    print("=" * 60)

    for result in results:

        print(f"\nRank: {result['rank']}")
        print(f"Score: {result['score']:.4f}")
        print(f"Chunk ID: {result['chunk_id']}")
        print(f"Source: {result['source']}")

        print("\nText:")
        print(result["text"])

        print("-" * 60)
