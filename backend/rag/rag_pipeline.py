from rag.retrieval.retriever import retrieve
from rag.generation.generator import generate_answer


def ask_rag(query, top_k=5):
    print("\n[1] Retrieving relevant chunks...")

    retrieved_chunks = retrieve(query, top_k=top_k)

    print(f"[2] Retrieved {len(retrieved_chunks)} chunks")

    print("[3] Generating answer with Gemini...")

    answer = generate_answer(
        query,
        retrieved_chunks
    )

    sources = [
        {
            "source": chunk["source"],
            "chunk_id": chunk["chunk_id"],
            "score": round(chunk["score"], 4)
        }
        for chunk in retrieved_chunks
    ]

    return {
        "answer": answer,
        "sources": sources
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
        print(
            f"{source['source']} | "
            f"Chunk {source['chunk_id']} | "
            f"Score {source['score']}"
        )

    print("=" * 80)
