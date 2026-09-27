"""PDF text cleaning and chunking.

pages -> drop repeated headers/footers -> detect section headings
      -> split each section into overlapping chunks

Chunks never cross a page boundary, so every chunk has an exact page
number that the UI can cite.
"""

import re
from collections import Counter


# Headings used in the knowledge-base PDFs, e.g.
#   "SECTION 7 — AYURVEDA AND PATENT SEARCHING"
#   "1.3 Major Classical Ayurveda Texts"
#   "V: International Agreements and Institutions"
#   "INTRODUCTION"
HEADING_PATTERN = re.compile(
    r"^(?:#\s*)?("
    r"SECTION \d+\s*[—–-]\s*\S.*"
    r"|\d+\.\d+(?:\.\d+)?\s+[A-Z].{2,90}"
    r"|[IVX]+:\s+[A-Z].{2,90}"
    r"|[A-Z][A-Z &,\-]{7,60}"
    r")$"
)

# A sentence ends at . ! ? ; or : followed by whitespace and a capital,
# digit, quote, bracket or bullet.
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?:;])\s+(?=[\"“(\[A-Z0-9•])")

# Bibliographies match almost every query on keywords but never answer one
SKIPPED_SECTIONS = {"REFERENCES", "BIBLIOGRAPHY"}


def _normalise_line(line):
    line = re.sub(r"\s+", " ", line).strip().lower()
    return re.sub(r"\d+", "#", line)


def remove_repeated_lines(pages, threshold=0.5, min_pages=3):
    """Drop lines that appear on more than `threshold` of the pages.

    These are running headers/footers such as journal names and
    "425 | Page" markers, which add noise to every chunk.
    """
    if len(pages) < min_pages:
        return pages

    counts = Counter()

    for page in pages:
        counts.update(
            {_normalise_line(line) for line in page.splitlines() if line.strip()}
        )

    repeated = {
        line
        for line, count in counts.items()
        if len(line) >= 4 and count / len(pages) > threshold
    }

    return [
        "\n".join(
            line
            for line in page.splitlines()
            if _normalise_line(line) not in repeated
        )
        for page in pages
    ]


def clean_text(text):
    text = text.replace("­", "")

    # "bio -piracy" -> "bio-piracy" (PDF extraction artefact)
    text = re.sub(r"(\w) -(\w)", r"\1-\2", text)

    return re.sub(r"\s+", " ", text).strip()


def _split_long_piece(text, chunk_size):
    words = text.split()
    pieces, current = [], []

    for word in words:
        if current and len(" ".join(current + [word])) > chunk_size:
            pieces.append(" ".join(current))
            current = []

        current.append(word)

    if current:
        pieces.append(" ".join(current))

    return pieces


def split_into_chunks(text, chunk_size, overlap):
    """Greedily pack whole sentences into chunks of at most `chunk_size`
    characters, repeating up to `overlap` characters of trailing sentences
    at the start of the next chunk."""
    pieces = []

    for sentence in SENTENCE_BOUNDARY.split(clean_text(text)):
        if not sentence:
            continue

        if len(sentence) <= chunk_size:
            pieces.append(sentence)
        else:
            pieces.extend(_split_long_piece(sentence, chunk_size))

    chunks, current = [], []

    for piece in pieces:
        if current and len(" ".join(current + [piece])) > chunk_size:
            chunks.append(" ".join(current))

            carry = []

            for previous in reversed(current):
                if len(" ".join([previous] + carry)) > overlap:
                    break

                carry.insert(0, previous)

            if len(" ".join(carry + [piece])) > chunk_size:
                carry = []

            current = carry

        current.append(piece)

    if current:
        chunks.append(" ".join(current))

    return chunks


def split_into_sections(pages):
    """Yield (page_number, section_heading, text) blocks.

    The current heading carries over to following pages until a new one
    appears.
    """
    section = None
    previous_was_heading = False

    for page_number, page in enumerate(pages, start=1):
        lines = []

        for raw_line in page.splitlines():
            line = raw_line.strip()
            match = HEADING_PATTERN.match(line)

            if match:
                heading = clean_text(match.group(1))

                if lines:
                    yield page_number, section, "\n".join(lines)
                    lines = []

                # A long all-caps heading can wrap onto a second line:
                # "SECTION 7 — AYURVEDA AND PATENT" + "SEARCHING"
                if previous_was_heading and section and section.isupper() and heading.isupper():
                    section = f"{section} {heading}"
                else:
                    section = heading

                previous_was_heading = True
            elif line:
                lines.append(line)
                previous_was_heading = False

        if lines:
            yield page_number, section, "\n".join(lines)


def chunk_document(pages, file, chunk_size, overlap, min_chars=60):
    """Turn a PDF's page texts into chunk dicts with page and section metadata."""
    pages = remove_repeated_lines(pages)
    chunks = []

    for page_number, section, text in split_into_sections(pages):
        if section in SKIPPED_SECTIONS:
            continue

        for chunk_text in split_into_chunks(text, chunk_size, overlap):
            if len(chunk_text) < min_chars:
                continue

            chunks.append({
                "file": file,
                "page": page_number,
                "section": section,
                "text": chunk_text,
            })

    return chunks


def searchable_text(chunk):
    """Text used for embeddings and BM25: the section heading gives each
    chunk context that its own text may not repeat."""
    if chunk.get("section"):
        return f"{chunk['section']}\n{chunk['text']}"

    return chunk["text"]
