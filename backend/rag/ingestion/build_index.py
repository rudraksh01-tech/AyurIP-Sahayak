"""Build the retrieval index from the PDFs in backend/data/raw.

Run from the project root:

    python -m backend.rag.ingestion.build_index            # chunk + embed
    python -m backend.rag.ingestion.build_index --dry-run  # chunk only, print stats

Writes backend/data/processed/index.json (chunks + metadata) and
backend/data/processed/embeddings.npy (one normalised vector per chunk).
"""

import argparse
import json

import numpy as np
from pypdf import PdfReader

from backend.rag import config
from backend.rag.gemini_client import embed_texts
from backend.rag.ingestion.chunking import chunk_document, searchable_text


def load_documents():
    sources = json.loads(config.SOURCES_PATH.read_text(encoding="utf-8"))
    documents, chunks = [], []

    for pdf_path in sorted(config.RAW_DIR.glob("*.pdf")):
        meta = sources.get(pdf_path.name, {})
        fallback_title = pdf_path.stem.replace("-", " ").title()

        pages = [page.extract_text() or "" for page in PdfReader(pdf_path).pages]

        doc_chunks = chunk_document(
            pages,
            file=pdf_path.name,
            chunk_size=config.CHUNK_SIZE,
            overlap=config.CHUNK_OVERLAP,
        )

        documents.append({
            "file": pdf_path.name,
            "title": meta.get("title", fallback_title),
            "short_title": meta.get("short_title", fallback_title),
            "author": meta.get("author"),
            "pages": len(pages),
            "chunks": len(doc_chunks),
        })

        chunks.extend(doc_chunks)

    for chunk_id, chunk in enumerate(chunks):
        chunk["id"] = chunk_id

    return documents, chunks


def print_stats(documents, chunks):
    lengths = [len(chunk["text"]) for chunk in chunks]

    for document in documents:
        print(
            f"{document['file']}: {document['pages']} pages -> "
            f"{document['chunks']} chunks"
        )

    print(
        f"Total: {len(chunks)} chunks | "
        f"avg {sum(lengths) // len(lengths)} chars | "
        f"min {min(lengths)} | max {max(lengths)}"
    )


def embed_chunks(documents, chunks):
    matrices = []

    # Embed one document at a time so Gemini gets the document title,
    # which improves RETRIEVAL_DOCUMENT embeddings.
    for document in documents:
        texts = [
            searchable_text(chunk)
            for chunk in chunks
            if chunk["file"] == document["file"]
        ]

        print(f"Embedding {len(texts)} chunks from {document['file']}...")

        matrices.append(
            embed_texts(texts, "RETRIEVAL_DOCUMENT", title=document["title"])
        )

    return np.vstack(matrices)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="chunk the PDFs and print stats without calling Gemini",
    )
    args = parser.parse_args()

    documents, chunks = load_documents()
    print_stats(documents, chunks)

    if args.dry_run:
        return

    embeddings = embed_chunks(documents, chunks)

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    index = {
        "embedding_model": config.EMBEDDING_MODEL,
        "dimensions": config.EMBEDDING_DIMENSIONS,
        "chunk_size": config.CHUNK_SIZE,
        "chunk_overlap": config.CHUNK_OVERLAP,
        "documents": documents,
        "chunks": chunks,
    }

    config.INDEX_PATH.write_text(
        json.dumps(index, ensure_ascii=False, indent=1),
        encoding="utf-8",
    )
    np.save(config.EMBEDDINGS_PATH, embeddings)

    print(f"Saved {config.INDEX_PATH}")
    print(f"Saved {config.EMBEDDINGS_PATH} {embeddings.shape}")


if __name__ == "__main__":
    main()
