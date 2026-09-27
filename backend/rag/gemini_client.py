"""Thin wrapper around the Gemini API: one lazily created client, embeddings and generation."""

import os
import time
from functools import lru_cache

import numpy as np
from google import genai
from google.genai import errors, types

from backend.rag import config


class GeminiConfigError(RuntimeError):
    """Raised when the server has no Gemini API key configured."""


@lru_cache(maxsize=1)
def get_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise GeminiConfigError(
            "GEMINI_API_KEY is not set. Add it to the project-root .env "
            "(see .env.example) or to your hosting provider's environment variables."
        )

    return genai.Client(api_key=api_key)


def _with_retry(call, attempts=5):
    """Retry on rate limits (HTTP 429) with exponential backoff."""
    for attempt in range(attempts):
        try:
            return call()
        except errors.APIError as error:
            if error.code != 429 or attempt == attempts - 1:
                raise

            wait_seconds = 2 ** attempt * 5
            print(f"Rate limited by Gemini, retrying in {wait_seconds}s...")
            time.sleep(wait_seconds)


def embed_texts(texts, task_type, title=None, batch_size=50):
    """Embed texts and return an L2-normalised float32 matrix (one row per text).

    task_type is "RETRIEVAL_DOCUMENT" for chunks and "RETRIEVAL_QUERY" for questions.
    """
    client = get_client()
    vectors = []

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]

        result = _with_retry(
            lambda: client.models.embed_content(
                model=config.EMBEDDING_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    title=title,
                    output_dimensionality=config.EMBEDDING_DIMENSIONS,
                ),
            )
        )

        vectors.extend(embedding.values for embedding in result.embeddings)

    matrix = np.asarray(vectors, dtype=np.float32)

    # gemini-embedding-001 only normalises full-size (3072-d) vectors,
    # so truncated vectors must be normalised for cosine similarity.
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)

    return matrix / np.clip(norms, 1e-12, None)


def generate_stream(prompt, system_instruction):
    """Yield the answer text piece by piece as Gemini produces it."""
    stream = get_client().interactions.create(
        model=config.GENERATION_MODEL,
        input=prompt,
        system_instruction=system_instruction,
        generation_config={"thinking_level": config.THINKING_LEVEL},
        store=False,
        stream=True,
    )

    for event in stream:
        if event.event_type == "error":
            raise RuntimeError(f"Gemini stream error: {event.error}")

        delta = getattr(event, "delta", None)

        # Other deltas (thought signatures, tool calls) are not part of the answer
        if event.event_type == "step.delta" and getattr(delta, "type", None) == "text":
            yield delta.text
