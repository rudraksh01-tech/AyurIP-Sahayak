import json
import math
import re
from collections import Counter
from pathlib import Path

EMBEDDINGS_PATH = Path("data/processed/embeddings.json")

print("Loading knowledge base...")

with open(EMBEDDINGS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total chunks loaded: {len(data)}")


def tokenize(text):
    return re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())


# Build a lightweight TF-IDF index.
documents = [tokenize(item["text"]) for item in data]

document_frequency = Counter()

for tokens in documents:
    for token in set(tokens):
        document_frequency[token] += 1

total_documents = len(documents)


def tfidf_score(query_tokens, document_tokens):
    if not query_tokens or not document_tokens:
        return 0.0

    document_counts = Counter(document_tokens)

    query_counts = Counter(query_tokens)

    score = 0.0

    for token, query_tf in query_counts.items():

        if token not in document_counts:
            continue

        df = document_frequency.get(token, 0)

        if df == 0:
            continue

        idf = math.log(
            (total_documents + 1) / (df + 1)
        ) + 1

        document_tf = document_counts[token]

        score += (
            (1 + math.log(query_tf))
            * (1 + math.log(document_tf))
            * (idf ** 2)
        )

    return score


def retrieve(query, top_k=5):

    print(f"\nQuery: {query}")

    query_tokens = tokenize(query)

    scored = []

    for index, document_tokens in enumerate(documents):

        score = tfidf_score(
            query_tokens,
            document_tokens
        )

        scored.append((score, index))

    scored.sort(
        key=lambda item: item[0],
        reverse=True
    )

    results = []

    for rank, (score, index) in enumerate(
        scored[:top_k],
        start=1
    ):

        item = data[index]

        results.append({
            "rank": rank,
            "score": float(score),
            "chunk_id": item["chunk_id"],
            "source": item["source"],
            "text": item["text"]
        })

    return results


if __name__ == "__main__":

    query = "What is Traditional Knowledge Digital Library TKDL?"

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
