import json
from pathlib import Path
from sentence_transformers import SentenceTransformer

CHUNKS_PATH = Path("data/processed/chunks.json")
OUTPUT_PATH = Path("data/processed/embeddings.json")

MODEL_NAME = "all-MiniLM-L6-v2"

print("Loading chunks...")
with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
    chunks = json.load(f)

print(f"Total chunks: {len(chunks)}")

print("Loading embedding model...")
model = SentenceTransformer(MODEL_NAME)

texts = [chunk["text"] for chunk in chunks]

print("Generating embeddings...")
embeddings = model.encode(
    texts,
    show_progress_bar=True,
    normalize_embeddings=True
)

output = []

for chunk, embedding in zip(chunks, embeddings):
    output.append({
        "chunk_id": chunk["chunk_id"],
        "source": chunk["source"],
        "chunk_index": chunk["chunk_index"],
        "text": chunk["text"],
        "embedding": embedding.tolist()
    })

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f)

print()
print("SUCCESS")
print(f"Saved: {OUTPUT_PATH}")
print(f"Embeddings: {len(output)}")
print(f"Embedding dimension: {len(output[0]['embedding'])}")
