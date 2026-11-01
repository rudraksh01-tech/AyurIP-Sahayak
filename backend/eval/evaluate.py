"""Compare BM25, dense (Gemini embeddings) and hybrid retrieval on a
labelled question set.

Run from the project root:

    python -m backend.eval.evaluate

A retrieved chunk counts as relevant when its section heading belongs to
one of the question's expected sections ("5.3" matches "5.3 ..." and
"5.3.1 ..."; "VI:" matches the journal's roman-numeral sections).
Results are printed as a Markdown table and saved to backend/eval/results.json.
"""

import json
from pathlib import Path

from backend.rag import config
from backend.rag.gemini_client import embed_texts
from backend.rag.retrieval.retriever import MODES, get_retriever


EVAL_DIR = Path(__file__).resolve().parent
QUESTIONS_PATH = EVAL_DIR / "questions.json"
RESULTS_PATH = EVAL_DIR / "results.json"

CUTOFFS = (1, 3, config.TOP_K)


def section_matches(section, expected):
    if not section:
        return False

    number = section.split()[0]

    return number == expected or number.startswith(expected + ".")


def is_relevant(result, expected_sections):
    return any(section_matches(result["section"], expected) for expected in expected_sections)


def first_relevant_rank(results, expected_sections):
    for rank, result in enumerate(results, start=1):
        if is_relevant(result, expected_sections):
            return rank

    return None


def score(ranks):
    return {
        **{
            f"hit@{k}": round(sum(1 for rank in ranks if rank and rank <= k) / len(ranks), 3)
            for k in CUTOFFS
        },
        "mrr": round(sum(1 / rank for rank in ranks if rank) / len(ranks), 3),
    }


def evaluate(questions, query_embeddings, retriever):
    """Return {group: {mode: metrics}} for "all" questions and each question type."""
    ranks = {mode: [] for mode in MODES}

    for item, embedding in zip(questions, query_embeddings):
        for mode in MODES:
            results = retriever.search(
                item["question"],
                top_k=config.TOP_K,
                mode=mode,
                query_embedding=embedding,
            )
            ranks[mode].append(first_relevant_rank(results, item["sections"]))

    groups = {"all": list(range(len(questions)))}

    for index, item in enumerate(questions):
        groups.setdefault(item.get("type", "general"), []).append(index)

    report = {}

    for group, indices in groups.items():
        report[group] = {
            "questions": len(indices),
            **{
                mode: score([ranks[mode][index] for index in indices])
                for mode in MODES
            },
        }

    report["misses"] = {
        mode: [
            item["question"]
            for item, rank in zip(questions, ranks[mode])
            if rank is None
        ]
        for mode in MODES
    }

    return report


def print_table(report):
    metrics = [f"hit@{k}" for k in CUTOFFS] + ["mrr"]
    header = " | ".join(metric.replace("hit", "Hit").replace("mrr", "MRR") for metric in metrics)

    for group, scores in report.items():
        if group == "misses":
            continue

        print(f"\n{group} ({scores['questions']} questions, top_k={config.TOP_K})\n")
        print(f"| Retriever | {header} |")
        print("|---" * (len(metrics) + 1) + "|")

        for mode in MODES:
            print(f"| {mode} | " + " | ".join(f"{scores[mode][metric]:.2f}" for metric in metrics) + " |")

    for mode, questions in report["misses"].items():
        if questions:
            print(f"\n{mode} found nothing relevant in the top {config.TOP_K} for:")

            for question in questions:
                print(f"  - {question}")


def main():
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    retriever = get_retriever()

    # One batched call instead of one embedding request per question
    query_embeddings = embed_texts(
        [item["question"] for item in questions],
        "RETRIEVAL_QUERY",
    )

    report = evaluate(questions, query_embeddings, retriever)
    print_table(report)

    RESULTS_PATH.write_text(
        json.dumps({"top_k": config.TOP_K, **report}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nSaved {RESULTS_PATH}")


if __name__ == "__main__":
    main()
