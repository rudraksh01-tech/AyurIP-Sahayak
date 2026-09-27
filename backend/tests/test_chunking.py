from backend.rag.ingestion.chunking import (
    SENTENCE_BOUNDARY,
    chunk_document,
    clean_text,
    remove_repeated_lines,
    searchable_text,
    split_into_chunks,
    split_into_sections,
)


def test_remove_repeated_lines_drops_running_headers():
    bodies = ["Ayurveda basics.", "Patent law.", "TKDL overview.", "Case studies."]
    pages = [
        f"JOURNAL OF PHARMACEUTICAL SCIENCES {425 + i} | P a g e\n{body}"
        for i, body in enumerate(bodies)
    ]

    cleaned = remove_repeated_lines(pages)

    assert cleaned == bodies


def test_remove_repeated_lines_leaves_short_documents_alone():
    pages = ["Header\nOne", "Header\nTwo"]

    assert remove_repeated_lines(pages) == pages


def test_clean_text_fixes_split_hyphens_and_whitespace():
    assert clean_text("bio -piracy  and\nbenefit -sharing ") == "bio-piracy and benefit-sharing"


def test_split_into_chunks_respects_size_and_overlaps_sentences():
    sentences = [f"Sentence {i} is about traditional knowledge." for i in range(40)]

    chunks = split_into_chunks(" ".join(sentences), chunk_size=200, overlap=60)

    assert len(chunks) > 1
    assert all(len(chunk) <= 200 for chunk in chunks)
    assert all(any(sentence in chunk for chunk in chunks) for sentence in sentences)

    for previous, current in zip(chunks, chunks[1:]):
        last_sentence = SENTENCE_BOUNDARY.split(previous)[-1]
        assert current.startswith(last_sentence)


def test_split_into_chunks_breaks_sentences_longer_than_chunk_size():
    text = " ".join(["word"] * 200)

    chunks = split_into_chunks(text, chunk_size=100, overlap=20)

    assert all(len(chunk) <= 100 for chunk in chunks)
    assert " ".join(chunks).split() == text.split()


def test_split_into_sections_carries_heading_across_pages():
    pages = [
        "SECTION 3 — TKDL\n3.1 What is TKDL?\nTKDL is a database.",
        "It was created in 2001.\n3.2 Why TKDL Was Created\nTo stop biopiracy.",
    ]

    assert list(split_into_sections(pages)) == [
        (1, "3.1 What is TKDL?", "TKDL is a database."),
        (2, "3.1 What is TKDL?", "It was created in 2001."),
        (2, "3.2 Why TKDL Was Created", "To stop biopiracy."),
    ]


def test_split_into_sections_joins_wrapped_all_caps_heading():
    pages = ["SECTION 7 — AYURVEDA AND PATENT\nSEARCHING\nStep one is to define the invention."]

    [(_, section, _)] = split_into_sections(pages)

    assert section == "SECTION 7 — AYURVEDA AND PATENT SEARCHING"


def test_chunk_document_adds_metadata_and_skips_references():
    body = "Ayurveda is a traditional system of medicine from India. " * 5
    pages = [
        f"1.1 What is Ayurveda?\n{body}",
        "REFERENCES\n1. Sharma, A. (2019). A long citation that would otherwise become a chunk.",
    ]

    chunks = chunk_document(pages, file="kb.pdf", chunk_size=1000, overlap=100)

    assert len(chunks) == 1
    assert chunks[0]["file"] == "kb.pdf"
    assert chunks[0]["page"] == 1
    assert chunks[0]["section"] == "1.1 What is Ayurveda?"


def test_searchable_text_prefixes_section():
    chunk = {"section": "3.1 What is TKDL?", "text": "A database."}

    assert searchable_text(chunk) == "3.1 What is TKDL?\nA database."
    assert searchable_text({"section": None, "text": "A database."}) == "A database."
