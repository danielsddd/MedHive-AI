# FastAPI + ARQ worker image. Installs the Poetry-locked deps into the system environment,
# mounts the pre-pulled HuggingFace cache as a volume at runtime (compose) so no model is
# downloaded at boot, and defaults to uvicorn. The arq-worker service overrides the command.
# poetry.lock is copied alongside pyproject.toml and BEFORE the install step so Poetry
# installs exact pinned versions instead of re-resolving the whole dependency graph on
# every build — this is what makes the heavy torch/transformers stack fast to rebuild.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install "poetry>=1.8,<2.0"

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-interaction --no-ansi

COPY . .

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]