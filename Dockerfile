# Two stages: build the React app with Node, then run FastAPI on a slim
# Python image that serves both the API and the built frontend.

# ---------- 1. Frontend build ----------
FROM node:22-alpine AS frontend

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build


# ---------- 2. Runtime ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Only what the server needs at runtime: code and the prebuilt index
COPY backend/__init__.py backend/
COPY backend/app/ backend/app/
COPY backend/rag/ backend/rag/
COPY backend/data/processed/ backend/data/processed/
COPY --from=frontend /app/frontend/dist/ frontend/dist/

# Run as a non-root user
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

# GEMINI_API_KEY is passed at run time, never baked into the image:
#   docker run -p 8000:8000 -e GEMINI_API_KEY=... ayurip-sahayak
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
