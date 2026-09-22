"""Runtime configuration read from environment variables.

Everything that differs between a laptop, the CI and the AgentCore Runtime container is an
environment variable with a safe default; nothing here is a secret. Secrets (the Hugging Face
token, AWS credentials) are read by their own libraries from their standard locations.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_MODEL_ID = "eu.anthropic.claude-sonnet-5"
DEFAULT_REGION = "eu-central-1"


@dataclass(frozen=True)
class Settings:
    """Values the agent and the runtime need, resolved once at start-up."""

    model_id: str = DEFAULT_MODEL_ID
    region: str = DEFAULT_REGION
    log_level: str = "INFO"
    hf_cache_dir: str | None = None

    @classmethod
    def from_env(cls) -> Settings:
        """Build the settings from ``DEMOSIFT_*`` environment variables."""
        return cls(
            model_id=os.environ.get("DEMOSIFT_MODEL_ID", DEFAULT_MODEL_ID),
            region=os.environ.get("DEMOSIFT_REGION", DEFAULT_REGION),
            log_level=os.environ.get("DEMOSIFT_LOG_LEVEL", "INFO"),
            hf_cache_dir=os.environ.get("DEMOSIFT_HF_CACHE_DIR"),
        )
