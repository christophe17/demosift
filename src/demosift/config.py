"""Configuration read from environment variables.

The library needs almost none: where to cache what it downloads from the Hub, and how loud to
be. Nothing here is a secret; the Hugging Face token, when one is needed for a private dataset,
is read by ``huggingface_hub`` from its standard ``HF_TOKEN`` variable.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Values resolved once from ``DEMOSIFT_*`` environment variables."""

    log_level: str = "INFO"
    hf_cache_dir: str | None = None

    @classmethod
    def from_env(cls) -> Settings:
        """Build the settings from the environment."""
        return cls(
            log_level=os.environ.get("DEMOSIFT_LOG_LEVEL", "INFO"),
            hf_cache_dir=os.environ.get("DEMOSIFT_HF_CACHE_DIR"),
        )
