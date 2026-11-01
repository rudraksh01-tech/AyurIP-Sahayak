"""Relevance matching in the retrieval eval. No Gemini calls."""

from backend.eval.evaluate import first_relevant_rank, is_relevant


def result(section, file="kb.pdf", page=1):
    return {"section": section, "file": file, "page": page}


def test_section_prefix_matches_subsections_only():
    item = {"sections": ["5.3"]}

    assert is_relevant(result("5.3 Patentability"), item)
    assert is_relevant(result("5.3.1 Novelty"), item)
    assert not is_relevant(result("5.30 Other"), item)
    assert not is_relevant(result(None), item)


def test_page_labels_match_file_and_page():
    item = {"sections": [], "pages": {"guide.pdf": [21, 37]}}

    assert is_relevant(result(None, "guide.pdf", 37), item)
    assert not is_relevant(result(None, "guide.pdf", 38), item)
    assert not is_relevant(result(None, "kb.pdf", 37), item)


def test_first_relevant_rank_accepts_either_label():
    item = {"sections": ["10.1"], "pages": {"guide.pdf": [21]}}
    results = [result("2.1 Other"), result(None, "guide.pdf", 21), result("10.1 Turmeric")]

    assert first_relevant_rank(results, item) == 2
    assert first_relevant_rank(results[:1], item) is None
