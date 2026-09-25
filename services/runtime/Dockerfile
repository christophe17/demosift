# AgentCore Runtime container: linux/arm64, Python 3.12, the demosift package and its locked
# dependencies, serving POST /invocations and GET /ping on port 8080 via the bedrock_agentcore SDK.
# Build from the repository root: docker build --platform linux/arm64 -f services/runtime/Dockerfile .

FROM python:3.12-slim-bookworm AS runtime

COPY --from=ghcr.io/astral-sh/uv:0.11.13 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first, so source edits do not invalidate the dependency layer.
COPY pyproject.toml uv.lock README.md LICENSE ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# Runtime user: no root inside the container; the Hub cache lives in a writable directory.
RUN useradd --system --uid 10001 --create-home --home-dir /home/demosift demosift \
    && mkdir -p /home/demosift/hf-cache && chown -R demosift:demosift /home/demosift
USER demosift

ENV PATH="/app/.venv/bin:$PATH" \
    DEMOSIFT_HF_CACHE_DIR=/home/demosift/hf-cache \
    DEMOSIFT_REGION=eu-central-1 \
    DEMOSIFT_MODEL_ID=eu.anthropic.claude-sonnet-5 \
    DEMOSIFT_LOG_LEVEL=INFO \
    OTEL_PYTHON_DISTRO=aws_distro \
    OTEL_PYTHON_CONFIGURATOR=aws_configurator \
    OTEL_PYTHON_EXCLUDED_URLS="/ping"

EXPOSE 8080
# opentelemetry-instrument wires the ADOT auto-instrumentation (traces of every tool and model call); AgentCore
# Runtime supplies the exporter configuration. Locally, set OTEL_SDK_DISABLED=true to run without an exporter.
CMD ["opentelemetry-instrument", "python", "-m", "demosift.runtime"]
