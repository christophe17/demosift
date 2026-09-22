"""Level-0 inspection: what a dataset says about itself, and whether it is self-consistent.

The inspection reads only ``meta/`` and is fully deterministic: no model, no network beyond
the download. It answers "what is in this dataset?" (robot, cameras, tasks, episode lengths)
and runs the consistency checks that a broken upload fails (frame totals, contiguous
episode indices, video spans matching episode lengths). Frame-level audits (timestamp gaps,
frozen frames, action ranges) are milestone 1; they build on the same objects.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from demosift.format import DatasetMeta, load_meta

ROBUST_Z_THRESHOLD = 3.5
MAD_TO_SIGMA = 1.4826
VIDEO_SPAN_TOLERANCE_FRAMES = 1.0
MAX_LISTED_EPISODES = 10


class CameraInfo(BaseModel):
    """One camera stream as declared in the feature schema."""

    key: str
    height: int | None = None
    width: int | None = None
    channels: int | None = None
    fps: float | None = None
    codec: str | None = None


class TaskInfo(BaseModel):
    """One task text with how many episodes and frames carry it."""

    task_index: int
    text: str
    episodes: int
    frames: int


class EpisodeLengths(BaseModel):
    """Distribution of episode lengths, in frames and seconds."""

    count: int
    min: int
    median: float
    max: int
    mean: float
    std: float
    total_frames: int
    total_seconds: float
    short_outliers: list[int] = Field(default_factory=list)
    long_outliers: list[int] = Field(default_factory=list)


class Check(BaseModel):
    """One consistency check with its verdict and a one-line explanation."""

    name: str
    passed: bool
    detail: str


class Inspection(BaseModel):
    """The level-0 report of a dataset."""

    dataset_id: str
    codebase_version: str
    robot_type: str | None
    fps: float
    total_episodes: int
    total_frames: int
    duration_seconds: float
    cameras: list[CameraInfo]
    state_dim: int | None
    action_dim: int | None
    state_names: list[str] | None
    action_names: list[str] | None
    tasks: list[TaskInfo]
    episode_lengths: EpisodeLengths
    checks: list[Check]

    @property
    def passed(self) -> bool:
        """Whether every consistency check passed."""
        return all(check.passed for check in self.checks)

    @property
    def failed_checks(self) -> list[Check]:
        """The checks that did not pass."""
        return [check for check in self.checks if not check.passed]


def _cameras(meta: DatasetMeta) -> list[CameraInfo]:
    cameras: list[CameraInfo] = []
    for key in meta.info.camera_keys:
        feature = meta.info.features[key]
        info = feature.video_info or {}
        height, width, channels = [*feature.shape, None, None, None][:3]
        cameras.append(
            CameraInfo(
                key=key,
                height=info.get("video.height", height),
                width=info.get("video.width", width),
                channels=info.get("video.channels", channels),
                fps=info.get("video.fps"),
                codec=info.get("video.codec"),
            )
        )
    return cameras


def _robust_outliers(lengths: pd.Series) -> tuple[list[int], list[int]]:
    """Episodes whose length is far from the median, in units of the median absolute deviation.

    The median and the MAD replace the mean and the standard deviation because a few very
    long or very short episodes would otherwise move the very statistics used to find them.
    """
    values = lengths.to_numpy(dtype=float)
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    if mad == 0.0:
        return [], []
    z = (values - median) / (MAD_TO_SIGMA * mad)
    episode_index = lengths.index.to_numpy()
    short = [int(i) for i in episode_index[z < -ROBUST_Z_THRESHOLD]]
    long = [int(i) for i in episode_index[z > ROBUST_Z_THRESHOLD]]
    return short, long


def _episode_lengths(meta: DatasetMeta) -> EpisodeLengths:
    lengths = meta.episodes.set_index("episode_index")["length"].astype(int)
    short, long = _robust_outliers(lengths)
    total = int(lengths.sum())
    return EpisodeLengths(
        count=int(lengths.size),
        min=int(lengths.min()),
        median=float(lengths.median()),
        max=int(lengths.max()),
        mean=float(lengths.mean()),
        std=float(lengths.std(ddof=0)),
        total_frames=total,
        total_seconds=total / meta.info.fps,
        short_outliers=short,
        long_outliers=long,
    )


def _tasks(meta: DatasetMeta) -> list[TaskInfo]:
    texts = meta.task_texts
    episodes_per_task: dict[str, int] = dict.fromkeys(texts.values(), 0)
    frames_per_task: dict[str, int] = dict.fromkeys(texts.values(), 0)
    for tasks, length in zip(meta.episodes["tasks"], meta.episodes["length"], strict=True):
        for text in list(tasks):
            episodes_per_task[text] = episodes_per_task.get(text, 0) + 1
            frames_per_task[text] = frames_per_task.get(text, 0) + int(length)
    return [
        TaskInfo(
            task_index=index,
            text=text,
            episodes=episodes_per_task.get(text, 0),
            frames=frames_per_task.get(text, 0),
        )
        for index, text in sorted(texts.items())
    ]


def _checks(meta: DatasetMeta) -> list[Check]:
    info, episodes = meta.info, meta.episodes
    checks: list[Check] = []

    frames = int(episodes["length"].sum())
    checks.append(
        Check(
            name="frame_total_matches",
            passed=frames == info.total_frames,
            detail=f"episode lengths sum to {frames}, info.json declares {info.total_frames}",
        )
    )
    checks.append(
        Check(
            name="episode_count_matches",
            passed=len(episodes) == info.total_episodes,
            detail=f"{len(episodes)} episode rows, info.json declares {info.total_episodes}",
        )
    )
    indices = episodes["episode_index"].to_numpy()
    contiguous = bool(np.array_equal(indices, np.arange(len(indices))))
    checks.append(
        Check(
            name="episode_indices_contiguous",
            passed=contiguous,
            detail="episode_index runs 0..N-1 without gaps"
            if contiguous
            else "episode_index has gaps or duplicates",
        )
    )
    checks.append(
        Check(
            name="fps_positive",
            passed=info.fps > 0,
            detail=f"fps = {info.fps}",
        )
    )
    empty = [int(i) for i, n in zip(indices, episodes["length"], strict=True) if int(n) <= 0]
    checks.append(
        Check(
            name="no_empty_episode",
            passed=not empty,
            detail="every episode has at least one frame"
            if not empty
            else f"empty episodes: {empty}",
        )
    )
    known = set(meta.task_texts.values())
    unknown = sorted({t for tasks in episodes["tasks"] for t in list(tasks) if t not in known})
    missing = [
        int(i) for i, tasks in zip(indices, episodes["tasks"], strict=True) if len(list(tasks)) == 0
    ]
    checks.append(
        Check(
            name="every_episode_has_known_task",
            passed=not unknown and not missing,
            detail="every episode carries at least one task listed in tasks.parquet"
            if not unknown and not missing
            else f"episodes without task: {missing}; task texts not in tasks.parquet: {unknown}",
        )
    )
    for key in info.camera_keys:
        start, end = f"videos/{key}/from_timestamp", f"videos/{key}/to_timestamp"
        if start not in episodes.columns or end not in episodes.columns:
            checks.append(
                Check(
                    name=f"video_span_matches_length[{key}]",
                    passed=False,
                    detail=f"no video span columns for {key} in the episode metadata",
                )
            )
            continue
        span_frames = (episodes[end] - episodes[start]).to_numpy(dtype=float) * info.fps
        gap = np.abs(span_frames - episodes["length"].to_numpy(dtype=float))
        bad = [int(i) for i, g in zip(indices, gap, strict=True) if g > VIDEO_SPAN_TOLERANCE_FRAMES]
        ellipsis = "…" if len(bad) > MAX_LISTED_EPISODES else ""
        listed = f"{bad[:MAX_LISTED_EPISODES]}{ellipsis}"
        checks.append(
            Check(
                name=f"video_span_matches_length[{key}]",
                passed=not bad,
                detail=(
                    "video spans match episode lengths within "
                    f"{VIDEO_SPAN_TOLERANCE_FRAMES:g} frame"
                    if not bad
                    else f"span/length mismatch beyond {VIDEO_SPAN_TOLERANCE_FRAMES:g} frame "
                    f"in episodes {listed}"
                ),
            )
        )
    return checks


def inspect_meta(meta: DatasetMeta, dataset_id: str) -> Inspection:
    """Build the level-0 inspection from parsed metadata."""
    info = meta.info
    state = info.features.get("observation.state")
    action = info.features.get("action")
    lengths = _episode_lengths(meta)
    return Inspection(
        dataset_id=dataset_id,
        codebase_version=info.codebase_version,
        robot_type=info.robot_type,
        fps=info.fps,
        total_episodes=info.total_episodes,
        total_frames=info.total_frames,
        duration_seconds=info.total_frames / info.fps,
        cameras=_cameras(meta),
        state_dim=info.vector_dim("observation.state"),
        action_dim=info.vector_dim("action"),
        state_names=state.flat_names if state else None,
        action_names=action.flat_names if action else None,
        tasks=_tasks(meta),
        episode_lengths=lengths,
        checks=_checks(meta),
    )


def inspect_root(root: Path, dataset_id: str | None = None) -> Inspection:
    """Load ``meta/`` under ``root`` and inspect it."""
    root = Path(root)
    return inspect_meta(load_meta(root), dataset_id or root.name)
