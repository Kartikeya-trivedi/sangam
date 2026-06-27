# SETU backend — single Python image built with uv (spec §4: one artifact ships).
FROM python:3.11-slim

# uv binary — fast, reproducible installs.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# System libs for pillow / faiss / (optional) onnxruntime.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend

# Install deps first for layer caching. Core only by default — face matching degrades
# gracefully (§13). On a GPU host, build with face matching: add `--extra faces` below.
COPY backend/pyproject.toml ./
RUN uv sync --no-dev

# App + seed script.
COPY backend/ ./
COPY scripts/ /app/scripts/

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
