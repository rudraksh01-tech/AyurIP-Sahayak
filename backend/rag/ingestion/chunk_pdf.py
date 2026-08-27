from pathlib import Path
import json

from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


# Input PDF folder
PDF_DIR = Path("data/raw")

# Output folder
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# Text splitter
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100
)


# Find all PDFs
pdf_files = list(PDF_DIR.glob("*.pdf"))

print(f"Found {len(pdf_files)} PDF files")


all_chunks = []


for pdf_path in pdf_files:

    print("\n" + "=" * 60)
    print(f"Processing: {pdf_path.name}")

    reader = PdfReader(pdf_path)

    text = ""

    # Extract text from every page
    for page_number, page in enumerate(reader.pages, start=1):

        page_text = page.extract_text() or ""

        if page_text:
            text += page_text + "\n"

    # Create chunks
    chunks = splitter.split_text(text)

    print(f"Pages: {len(reader.pages)}")
    print(f"Total characters: {len(text)}")
    print(f"Total chunks: {len(chunks)}")

    # Store chunks with metadata
    for i, chunk in enumerate(chunks):

        all_chunks.append({
            "chunk_id": len(all_chunks),
            "source": pdf_path.name,
            "chunk_index": i,
            "text": chunk
        })


# Save all chunks
output_file = OUTPUT_DIR / "chunks.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, ensure_ascii=False, indent=2)


print("\n" + "=" * 60)
print(f"Total chunks from all PDFs: {len(all_chunks)}")
print(f"Saved to: {output_file}")