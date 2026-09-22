"""Reading the LeRobot dataset format (codebase ``v3.0``) from its metadata files.

The layout was observed on real Hub datasets on 2026-09-21 (``lerobot/svla_so101_pickplace``,
``lerobot/aloha_sim_insertion_human``)::

    meta/info.json                          dataset-level description and the feature schema
    meta/stats.json                         per-feature min/max/mean/std/count over the dataset
    meta/tasks.parquet                      one row per task text, column ``task_index``
    meta/episodes/chunk-XXX/file-XXX.parquet  one row per episode: length, tasks, file pointers,
                                            per-camera video spans, per-feature statistics
    data/chunk-XXX/file-XXX.parquet         one row per frame: state, action, timestamps, indices
    videos/<camera>/chunk-XXX/file-XXX.mp4  several episodes concatenated per file

This module only reads ``meta/``; frame-level data is milestone 1.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

SUPPORTED_VERSIONS: tuple[str, ...] = ("v3.0",)
IMAGE_DTYPES: tuple[str, ...] = ("video", "image")


class UnsupportedFormatError(ValueError):
    """The dataset uses a codebase version this tool does not read."""


class Feature(BaseModel):
    """One entry of ``info.json``'s ``features`` map."""

    model_config = ConfigDict(extra="allow", populate_by_name=True)

    dtype: str
    shape: list[int]
    names: Any | None = None
    video_info: dict[str, Any] | None = Field(default=None, alias="info")

    @property
    def is_visual(self) -> bool:
        """Whether the feature is a camera stream (stored as video or as image files)."""
        return self.dtype in IMAGE_DTYPES

    @property
    def flat_names(self) -> list[str] | None:
        """The per-dimension names, when ``names`` is a plain list of strings."""
        if isinstance(self.names, list) and all(isinstance(n, str) for n in self.names):
            return list(self.names)
        return None


class DatasetInfo(BaseModel):
    """The content of ``meta/info.json``."""

    model_config = ConfigDict(extra="allow")

    codebase_version: str
    robot_type: str | None = None
    total_episodes: int
    total_frames: int
    total_tasks: int | None = None
    fps: float
    splits: dict[str, str] = Field(default_factory=dict)
    data_path: str
    video_path: str | None = None
    chunks_size: int | None = None
    features: dict[str, Feature]

    @property
    def camera_keys(self) -> list[str]:
        """Feature keys that are camera streams, in schema order."""
        return [key for key, feature in self.features.items() if feature.is_visual]

    def vector_dim(self, key: str) -> int | None:
        """Length of a one-dimensional feature such as ``action``; ``None`` if absent."""
        feature = self.features.get(key)
        if feature is None or len(feature.shape) != 1:
            return None
        return feature.shape[0]


@dataclass(frozen=True)
class DatasetMeta:
    """Everything under ``meta/``, parsed."""

    root: Path
    info: DatasetInfo
    tasks: pd.DataFrame
    episodes: pd.DataFrame
    stats: dict[str, Any] | None

    @property
    def task_texts(self) -> dict[int, str]:
        """Map ``task_index`` to the task text."""
        return {int(index): str(text) for text, index in self.tasks["task_index"].items()}


def read_info(root: Path) -> DatasetInfo:
    """Parse ``meta/info.json`` and refuse unsupported codebase versions."""
    info = DatasetInfo.model_validate(json.loads((root / "meta" / "info.json").read_text()))
    if info.codebase_version not in SUPPORTED_VERSIONS:
        msg = (
            f"codebase_version {info.codebase_version!r} is not supported "
            f"(supported: {', '.join(SUPPORTED_VERSIONS)})"
        )
        raise UnsupportedFormatError(msg)
    return info


def read_tasks(root: Path) -> pd.DataFrame:
    """Parse ``meta/tasks.parquet``: the task text is the index, ``task_index`` the column."""
    tasks = pd.read_parquet(root / "meta" / "tasks.parquet")
    if "task_index" not in tasks.columns:
        msg = "meta/tasks.parquet has no task_index column"
        raise UnsupportedFormatError(msg)
    return tasks


def read_episodes(root: Path) -> pd.DataFrame:
    """Concatenate every ``meta/episodes/chunk-*/file-*.parquet`` in episode order."""
    files = sorted((root / "meta" / "episodes").glob("chunk-*/file-*.parquet"))
    if not files:
        msg = "no episode metadata files under meta/episodes/"
        raise UnsupportedFormatError(msg)
    episodes = pd.concat([pd.read_parquet(path) for path in files], ignore_index=True)
    return episodes.sort_values("episode_index").reset_index(drop=True)


def read_stats(root: Path) -> dict[str, Any] | None:
    """Parse ``meta/stats.json`` when present."""
    path = root / "meta" / "stats.json"
    if not path.exists():
        return None
    stats: dict[str, Any] = json.loads(path.read_text())
    return stats


def load_meta(root: Path) -> DatasetMeta:
    """Read the whole ``meta/`` directory of a dataset stored under ``root``."""
    root = Path(root)
    return DatasetMeta(
        root=root,
        info=read_info(root),
        tasks=read_tasks(root),
        episodes=read_episodes(root),
        stats=read_stats(root),
    )
