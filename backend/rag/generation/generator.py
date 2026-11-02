"""Prompt construction and answer generation with inline citations."""

import re
import unicodedata

from backend.rag.gemini_client import generate_stream


SYSTEM_INSTRUCTION = """You are AyurIP Sahayak, a research assistant for Ayurveda, Traditional Knowledge (TK) and Intellectual Property Rights (IPR) in India.

Rules:
- Answer ONLY from the numbered context passages. Do not add outside knowledge.
- Cite the passages that support each statement with their numbers in square brackets, like [2] or [1][3]. Never cite a passage that does not support the statement.
- If the passages do not contain the answer, say clearly that the documents do not cover it, and suggest a related question they can answer. Do not guess.
- Write the whole answer in the ANSWER LANGUAGE given after the question, even if earlier turns used another language. Hinglish means Hindi written in English (Latin) letters.
- Write every word in one script. A technical English term may follow in brackets.
- Start with a direct answer in one or two sentences, then add short bullet points only if they help. Use Markdown bold and lists; no headings.
- Do not add disclaimers or notes about legal or medical advice; the app already shows one below every answer."""

CITATION_PATTERN = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")

# Devanagari and Kannada share one Unicode layout, 0x380 apart (क U+0915 -> ಕ U+0C95)
DEVANAGARI_TO_KANNADA = 0x380

# Common Hindi words written in Latin letters; two or more mark a question as Hinglish
HINGLISH_WORDS = {
    "kya", "kyun", "kyon", "kyu", "kaise", "kaun", "kab", "kahan", "kitna", "kitne",
    "hai", "hain", "tha", "thi", "hua", "hui", "ka", "ki", "ke", "ko", "se", "mein", "me",
    "aur", "nahi", "batao", "bataiye", "samjhao", "matlab", "wala", "wali", "karte", "karna",
}

MAX_HISTORY_TURNS = 6
MAX_HISTORY_CHARS = 600


def format_passage(number, result):
    location = f"{result['title']}, page {result['page']}"

    if result.get("section"):
        location += f" ({result['section']})"

    return f"[{number}] {location}\n{result['text']}"


def answer_language(question):
    """Pick the reply language from the question itself, not from the model's guess."""
    if is_kannada(question):
        return "Kannada (Kannada script)"

    if any("ऀ" <= char <= "ॿ" for char in question):
        return "Hindi (Devanagari script)"

    words = re.findall(r"[a-z]+", question.lower())

    if sum(word in HINGLISH_WORDS for word in words) >= 2:
        return "Hinglish (Hindi in Latin letters)"

    return "English"


def build_prompt(question, results, history=None):
    parts = []

    if history:
        turns = []

        for turn in history[-MAX_HISTORY_TURNS:]:
            speaker = "User" if turn["role"] == "user" else "Assistant"
            turns.append(f"{speaker}: {turn['content'][:MAX_HISTORY_CHARS]}")

        parts.append(
            "CONVERSATION SO FAR (use it only to understand follow-up questions):\n"
            + "\n".join(turns)
        )

    passages = "\n\n".join(
        format_passage(number, result)
        for number, result in enumerate(results, start=1)
    )

    parts.append(f"CONTEXT PASSAGES:\n{passages}")
    parts.append(f"QUESTION:\n{question}")
    parts.append(f"ANSWER LANGUAGE: {answer_language(question)}")

    return "\n\n".join(parts)


def find_citations(answer, passage_count):
    """Return the set of passage numbers cited in the answer, e.g. {1, 3}."""
    cited = set()

    for match in CITATION_PATTERN.finditer(answer):
        for number in match.group(1).split(","):
            number = int(number)

            if 1 <= number <= passage_count:
                cited.add(number)

    return cited


def is_kannada(text):
    return any("ಀ" <= char <= "೿" for char in text)


def to_kannada_script(text):
    """Replace Devanagari letters with the matching Kannada ones.

    In Kannada answers the model sometimes puts a Devanagari letter inside a
    Kannada word (ಸೈಂಟिफಿಕ್), which browsers draw as a broken glyph. Signs with
    no Kannada counterpart, such as the danda, are kept.
    """
    converted = []

    for char in text:
        if "ऀ" <= char <= "ॿ":
            kannada = chr(ord(char) + DEVANAGARI_TO_KANNADA)

            if unicodedata.name(kannada, None):
                char = kannada

        converted.append(char)

    return "".join(converted)


def stream_answer(question, results, history=None):
    """Yield the answer text in pieces as it is generated."""
    if not results:
        yield "I couldn't find anything relevant to that in the knowledge base."
        return

    pieces = generate_stream(
        build_prompt(question, results, history),
        SYSTEM_INSTRUCTION,
    )

    if is_kannada(question):
        pieces = (to_kannada_script(piece) for piece in pieces)

    yield from pieces
