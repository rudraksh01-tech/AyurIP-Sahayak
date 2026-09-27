"""Central configuration: paths, model names and retrieval settings."""

import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_DIR.parent

# Local development reads the project-root .env; on Vercel the variables
# come from the project settings and this is a no-op.
load_dotenv(PROJECT_ROOT / ".env")


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

RAW_DIR = BACKEND_DIR / "data" / "raw"
SOURCES_PATH = RAW_DIR / "sources.json"

PROCESSED_DIR = BACKEND_DIR / "data" / "processed"
INDEX_PATH = PROCESSED_DIR / "index.json"
EMBEDDINGS_PATH = PROCESSED_DIR / "embeddings.npy"

FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"


# ---------------------------------------------------------
# MODELS
# ---------------------------------------------------------

# flash-lite with minimal thinking streams its first words in ~2s versus
# ~8-10s for gemini-3.6-flash, with the same answer quality on this task.
GENERATION_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
THINKING_LEVEL = os.getenv("GEMINI_THINKING_LEVEL", "minimal")

# The stored index is tied to this model; rebuild the index if you change it.
EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


# ---------------------------------------------------------
# CHUNKING & RETRIEVAL
# ---------------------------------------------------------

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

TOP_K = 6

# "dense" (Gemini embeddings), "bm25" (keywords) or "hybrid" (both, fused
# with RRF). Dense scored best on backend/eval (MRR 0.98 vs 0.93 hybrid
# and 0.66 BM25), so it is the default; run the eval again after changing
# the documents.
RETRIEVAL_MODE = os.getenv("RETRIEVAL_MODE", "dense")

# How many candidates each retriever contributes before fusion
FUSION_CANDIDATES = 30

# Reciprocal Rank Fusion constant (60 is the value from the original paper)
RRF_K = 60


# ---------------------------------------------------------
# API
# ---------------------------------------------------------

RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
