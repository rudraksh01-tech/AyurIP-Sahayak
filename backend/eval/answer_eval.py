"""Answer-quality evaluation with an LLM judge.

Run from the project root (needs GEMINI_API_KEY for the answers and
GROQ_API_KEY for the judge):

    python -m backend.eval.answer_eval                 # answer + judge
    python -m backend.eval.answer_eval --answers-only  # just generate and cache the answers

For every question in questions.json the app answers as usual, then a judge
model from a different provider (openai/gpt-oss-120b on Groq) splits the
answer into claims and checks each one against the retrieved passages. A
judge from another model family can't favour its own writing style, and
Groq's free tier allows far more requests than the larger Gemini models.

Three extra checks keep the numbers honest:

- unanswerable.json holds questions the documents don't cover; the app
  should say so instead of answering.
- A false sentence with a citation is added to some real answers; the judge
  should flag it. This measures the judge, not the app.
- Every judgement is saved to answer_results.json so it can be read by hand.

Answers and judgements are cached in answer_cache.json (git-ignored), so a
run stopped by a rate limit continues where it left off.
"""

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from google.genai import errors

from backend.rag.generation.generator import format_passage
from backend.rag.rag_pipeline import ask_rag


EVAL_DIR = Path(__file__).resolve().parent
QUESTIONS_PATH = EVAL_DIR / "questions.json"
UNANSWERABLE_PATH = EVAL_DIR / "unanswerable.json"
RESULTS_PATH = EVAL_DIR / "answer_results.json"
CACHE_PATH = EVAL_DIR / "answer_cache.json"

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-oss-120b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# How many real answers get a false sentence added for the judge check
INJECTED_ANSWERS = 15

# False statements on the knowledge base's topics, each cited as if a passage supported it
FALSE_CLAIMS = [
    "The Traditional Knowledge Digital Library was set up by the World Health Organization in 1975 [1].",
    "The European Patent Office upheld the neem patent in full and it is still in force [1].",
    "Section 3(p) of the Indian Patents Act allows traditional knowledge to be patented without any restriction [1].",
    "The full TKDL database, including all its translations, is freely open to the general public [1].",
    "Ayurveda originated in ancient Egypt and reached India in the 18th century [1].",
]

JUDGE_INSTRUCTIONS = """You are grading an answer written by a retrieval-augmented assistant.
You get the numbered passages the assistant was given, the user's question and the assistant's answer.

1. Split the answer into its factual claims (one short sentence each). Skip greetings and
   statements like "the documents do not cover this".
2. For each claim, list the passage numbers the answer cites for it ([n] markers next to it).
3. supported_by_cited: true only if the cited passages state or directly imply the claim.
   False if nothing is cited.
4. supported_by_any: true if ANY of the passages states or directly implies the claim.
   Judge only against the passages, not your own knowledge.
5. refused: true if the answer mainly says the documents don't cover the question.
6. answers_question: true if the answer actually addresses what was asked.

Be strict: a claim with a wrong date, number, name or outcome is not supported."""

JUDGE_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "cited": {"type": "array", "items": {"type": "integer"}},
                    "supported_by_cited": {"type": "boolean"},
                    "supported_by_any": {"type": "boolean"},
                },
                "required": ["claim", "cited", "supported_by_cited", "supported_by_any"],
                "additionalProperties": False,
            },
        },
        "refused": {"type": "boolean"},
        "answers_question": {"type": "boolean"},
    },
    "required": ["claims", "refused", "answers_question"],
    "additionalProperties": False,
}


# ---------------------------------------------------------
# JUDGE
# ---------------------------------------------------------

def build_judge_prompt(question, answer, sources):
    passages = "\n\n".join(format_passage(source["number"], source) for source in sources)

    return (
        f"PASSAGES:\n{passages}\n\n"
        f"QUESTION:\n{question}\n\n"
        f"ANSWER:\n{answer}"
    )


def groq_json(system, prompt, attempts=6):
    """Call Groq's OpenAI-compatible API and return the reply parsed as JSON."""
    api_key = (os.getenv("GROQ_API_KEY") or "").strip()

    if not api_key:
        sys.exit("GROQ_API_KEY is not set. Add a free key from https://console.groq.com/keys to .env.")

    body = json.dumps({
        "model": JUDGE_MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": "judgement", "schema": JUDGE_SCHEMA, "strict": True},
        },
    }).encode()

    for attempt in range(attempts):
        request = urllib.request.Request(
            GROQ_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                # Groq's firewall rejects urllib's default User-Agent (Cloudflare error 1010)
                "User-Agent": "ayurip-sahayak-eval/1.0",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                reply = json.load(response)
            return json.loads(reply["choices"][0]["message"]["content"])
        except urllib.error.HTTPError as error:
            if error.code not in (429, 500, 503) or attempt == attempts - 1:
                raise

            # Groq says how long to wait when a per-minute token budget is used up
            wait_seconds = float(error.headers.get("retry-after") or 2 ** attempt * 5)
            print(f"Groq returned {error.code}, retrying in {wait_seconds:.0f}s...")
            time.sleep(wait_seconds)


def judge(question, answer, sources, cache):
    key = hashlib.sha256(f"{JUDGE_MODEL}\n{question}\n{answer}".encode()).hexdigest()

    if key not in cache["judgements"]:
        cache["judgements"][key] = groq_json(
            JUDGE_INSTRUCTIONS, build_judge_prompt(question, answer, sources)
        )
        save_cache(cache)

    return cache["judgements"][key]


# ---------------------------------------------------------
# SCORING
# ---------------------------------------------------------

def score_judgement(judgement):
    """Per-answer scores from one judgement; None where a score doesn't apply."""
    claims = judgement["claims"]
    cited = [claim for claim in claims if claim["cited"]]

    return {
        "claims": len(claims),
        "faithfulness": (
            sum(claim["supported_by_any"] for claim in claims) / len(claims) if claims else None
        ),
        "citation_precision": (
            sum(claim["supported_by_cited"] for claim in cited) / len(cited) if cited else None
        ),
        "citation_coverage": len(cited) / len(claims) if claims else None,
        "fully_faithful": all(claim["supported_by_any"] for claim in claims),
        "refused": judgement["refused"],
        "answers_question": judgement["answers_question"],
    }


def mean(values):
    values = [value for value in values if value is not None]
    return round(sum(values) / len(values), 3) if values else None


def summarize(answerable, unanswerable, injected):
    """Combine per-question scores into the headline numbers."""
    answered = [score for score in answerable if not score["refused"]]

    return {
        "answerable": {
            "questions": len(answerable),
            "answered": len(answered),
            "refused": len(answerable) - len(answered),
            "answers_question": sum(score["answers_question"] for score in answered),
            "faithfulness": mean(score["faithfulness"] for score in answered),
            "fully_faithful_answers": sum(score["fully_faithful"] for score in answered),
            "citation_precision": mean(score["citation_precision"] for score in answered),
            "citation_coverage": mean(score["citation_coverage"] for score in answered),
            "claims": sum(score["claims"] for score in answered),
        },
        "unanswerable": {
            "questions": len(unanswerable),
            "correctly_refused": sum(score["refused"] for score in unanswerable),
        },
        "judge_check": {
            "false_claims_added": len(injected),
            "caught": sum(injected),
        },
    }


def inject_false_claim(answer, false_claim):
    return f"{answer.rstrip()}\n\n{false_claim}"


def false_claim_caught(judgement, false_claim):
    """True if the judge marked the added sentence (or a claim from it) as unsupported."""
    key_words = {word.strip(".,[]()").lower() for word in false_claim.split() if len(word) > 5}

    for claim in judgement["claims"]:
        words = {word.strip(".,[]()").lower() for word in claim["claim"].split()}

        if len(key_words & words) >= 2 and not claim["supported_by_any"]:
            return True

    return False


# ---------------------------------------------------------
# RUN
# ---------------------------------------------------------

def load_cache():
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text(encoding="utf-8"))

    return {"answers": {}, "judgements": {}}


def save_cache(cache):
    CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")


def ask_with_retry(question, attempts=5):
    """ask_rag streams, so the client's retry doesn't cover it; retry rate limits and overload here."""
    for attempt in range(attempts):
        try:
            return ask_rag(question)
        except errors.APIError as error:
            if error.code not in (429, 503) or attempt == attempts - 1:
                raise

            wait_seconds = 2 ** attempt * 5
            print(f"Gemini returned {error.code}, retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)


def answer_all(items, cache):
    for number, item in enumerate(items, start=1):
        if item["question"] not in cache["answers"]:
            result = ask_with_retry(item["question"])
            cache["answers"][item["question"]] = {
                "answer": result["answer"],
                "sources": result["sources"],
            }
            save_cache(cache)

        print(f"  answered {number}/{len(items)}: {item['question'][:60]}")


def judge_all(items, cache):
    records = []

    for number, item in enumerate(items, start=1):
        cached = cache["answers"][item["question"]]
        judgement = judge(item["question"], cached["answer"], cached["sources"], cache)
        records.append({
            "question": item["question"],
            "type": item.get("type", "general"),
            "answer": cached["answer"],
            "judgement": judgement,
            "scores": score_judgement(judgement),
            "sources": [
                {key: source[key] for key in ("number", "title", "page", "section")}
                for source in cached["sources"]
            ],
        })
        print(f"  judged {number}/{len(items)}: {item['question'][:60]}")

    return records


def main():
    questions = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    unanswerable_questions = json.loads(UNANSWERABLE_PATH.read_text(encoding="utf-8"))
    cache = load_cache()

    print(f"Answering {len(questions) + len(unanswerable_questions)} questions")
    answer_all(questions + unanswerable_questions, cache)

    if "--answers-only" in sys.argv:
        print(f"Answers cached in {CACHE_PATH}")
        return

    print(f"Judging with {JUDGE_MODEL}")
    answerable = judge_all(questions, cache)
    unanswerable = judge_all(unanswerable_questions, cache)

    print(f"Adding a false sentence to {INJECTED_ANSWERS} answers to test the judge")
    injected = []

    for index, record in enumerate([r for r in answerable if not r["scores"]["refused"]][:INJECTED_ANSWERS]):
        false_claim = FALSE_CLAIMS[index % len(FALSE_CLAIMS)]
        answer = inject_false_claim(record["answer"], false_claim)
        sources = cache["answers"][record["question"]]["sources"]
        judgement = judge(record["question"], answer, sources, cache)
        injected.append({
            "question": record["question"],
            "false_claim": false_claim,
            "caught": false_claim_caught(judgement, false_claim),
            "judgement": judgement,
        })

    summary = summarize(
        [record["scores"] for record in answerable],
        [record["scores"] for record in unanswerable],
        [record["caught"] for record in injected],
    )

    print(json.dumps(summary, indent=2))

    for record in answerable:
        for claim in record["judgement"]["claims"]:
            if not claim["supported_by_any"]:
                print(f"\nUnsupported claim for: {record['question']}\n  - {claim['claim']}")

    RESULTS_PATH.write_text(
        json.dumps(
            {
                "judge_model": JUDGE_MODEL,
                "summary": summary,
                "answerable": answerable,
                "unanswerable": unanswerable,
                "judge_check": injected,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nSaved {RESULTS_PATH}")


if __name__ == "__main__":
    main()
