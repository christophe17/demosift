"""Fetching dataset files from the Hugging Face Hub, or using a local copy.

Only ``meta/`` is downloaded at this milestone: it is a few hundred kilobytes, while the
frame data and videos of a dataset weigh gigabytes. Milestone 1 adds selective downloads of
``data/`` chunks.
"""

from __future__ import annotations

from pathlib import Path

from huggingface_hub import snapshot_download

META_PATTERNS: tuple[str, ...] = ("meta/*", "meta/**")


def fetch_meta(
    dataset_id: str,
    *,
    revision: str | None = None,
    cache_dir: str | Path | None = None,
    token: str | None = None,
) -> Path:
    """Download the ``meta/`` directory of a Hub dataset and return the local snapshot root.

    Args:
        dataset_id: Hub identifier such as ``lerobot/svla_so101_pickplace``.
        revision: Git revision (branch, tag or commit); the default branch when ``None``.
        cache_dir: Where ``huggingface_hub`` stores snapshots; its default cache when ``None``.
        token: Hub token for private datasets; ``huggingface_hub`` reads the standard
            ``HF_TOKEN`` environment variable when ``None``.
    """
    return Path(
        snapshot_download(
            repo_id=dataset_id,
            repo_type="dataset",
            allow_patterns=list(META_PATTERNS),
            revision=revision,
            cache_dir=cache_dir,
            token=token,
        )
    )


def resolve_source(spec: str, *, cache_dir: str | Path | None = None) -> Path:
    """Return a local dataset root for ``spec``: an existing directory, else a Hub identifier."""
    local = Path(spec)
    if local.is_dir() and (local / "meta" / "info.json").exists():
        return local
    return fetch_meta(spec, cache_dir=cache_dir)
