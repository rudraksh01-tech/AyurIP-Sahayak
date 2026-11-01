"""Scoring logic of the answer-quality eval. No Gemini calls."""

from backend.eval.answer_eval import (
    FALSE_CLAIMS,
    false_claim_caught,
    inject_false_claim,
    score_judgement,
    summarize,
)


def claim(text, cited, by_cited, by_any):
    return {"claim": text, "cited": cited, "supported_by_cited": by_cited, "supported_by_any": by_any}


def test_score_judgement_counts_supported_and_cited_claims():
    judgement = {
        "claims": [
            claim("A", [1], True, True),
            claim("B", [2], False, True),   # true, but the wrong passage is cited
            claim("C", [], False, False),   # made up and uncited
            claim("D", [3], True, True),
        ],
        "refused": False,
        "answers_question": True,
    }

    scores = score_judgement(judgement)

    assert scores["claims"] == 4
    assert scores["faithfulness"] == 0.75
    assert scores["citation_precision"] == 2 / 3
    assert scores["citation_coverage"] == 0.75
    assert scores["fully_faithful"] is False


def test_refusal_without_claims_has_no_ratios():
    scores = score_judgement({"claims": [], "refused": True, "answers_question": False})

    assert scores["faithfulness"] is None
    assert scores["citation_precision"] is None
    assert scores["refused"] is True


def test_summarize_leaves_refused_answers_out_of_faithfulness():
    answered = score_judgement({"claims": [claim("A", [1], True, True)], "refused": False, "answers_question": True})
    refused = score_judgement({"claims": [], "refused": True, "answers_question": False})

    summary = summarize([answered, refused], [refused], [True, False])

    assert summary["answerable"]["answered"] == 1
    assert summary["answerable"]["refused"] == 1
    assert summary["answerable"]["faithfulness"] == 1.0
    assert summary["unanswerable"]["correctly_refused"] == 1
    assert summary["judge_check"] == {"false_claims_added": 2, "caught": 1}


def test_false_claim_is_appended_to_the_answer():
    answer = inject_false_claim("TKDL prevents wrongful patents [1].  ", FALSE_CLAIMS[0])

    assert answer.startswith("TKDL prevents wrongful patents [1].")
    assert answer.endswith(FALSE_CLAIMS[0])


def test_false_claim_caught_only_when_marked_unsupported():
    false_claim = FALSE_CLAIMS[0]
    rephrased = "TKDL was set up by the World Health Organization in 1975."

    flagged = {"claims": [claim(rephrased, [1], False, False)]}
    missed = {"claims": [claim(rephrased, [1], True, True)]}
    unrelated = {"claims": [claim("Neem has antifungal uses.", [2], False, False)]}

    assert false_claim_caught(flagged, false_claim)
    assert not false_claim_caught(missed, false_claim)
    assert not false_claim_caught(unrelated, false_claim)
