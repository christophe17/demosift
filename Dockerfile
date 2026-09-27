# The command line in a box: `docker run --rm ghcr.io/christophe17/demosift inspect <dataset>`.
# Multi-arch friendly; no port, no server, no cloud SDK. The hosted instance builds its own image
# on top of the published package, not on top of this one.
FROM python:3.12-slim-bookworm AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.11.13 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock README.md LICENSE ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

RUN useradd --system --uid 10001 --create-home --home-dir /home/demosift demosift \
    && mkdir -p /home/demosift/hf-cache && chown -R demosift:demosift /home/demosift
USER demosift

ENV PATH="/app/.venv/bin:$PATH" \
    DEMOSIFT_HF_CACHE_DIR=/home/demosift/hf-cache \
    DEMOSIFT_LOG_LEVEL=INFO

ENTRYPOINT ["demosift"]
CMD ["--help"]
