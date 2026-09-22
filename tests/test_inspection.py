import json
import shutil
from pathlib import Path

import pandas as pd

from demosift.inspection import inspect_root


def test_inspection_reports_real_facts(so101_root: Path) -> None:
    insp = inspect_root(so101_root, "lerobot/svla_so101_pickplace")
    assert insp.dataset_id == "lerobot/svla_so101_pickplace"
    assert insp.passed, [c.detail for c in insp.failed_checks]
    assert [c.key for c in insp.cameras] == ["observation.images.up", "observation.images.side"]
    assert (insp.cameras[0].width, insp.cameras[0].height, insp.cameras[0].fps) == (640, 480, 30)
    assert insp.state_dim == 6 and insp.action_dim == 6
    assert insp.tasks[0].text == "pink lego brick into the transparent box"
    assert insp.tasks[0].episodes == 50 and insp.tasks[0].frames == 11939
    assert insp.episode_lengths.count == 50
    assert insp.episode_lengths.total_frames == 11939
    assert abs(insp.duration_seconds - 11939 / 30) < 1e-9
    assert insp.episode_lengths.min <= insp.episode_lengths.median <= insp.episode_lengths.max


def test_every_camera_gets_a_video_span_check(so101_root: Path) -> None:
    insp = inspect_root(so101_root)
    names = {c.name for c in insp.checks}
    assert "video_span_matches_length[observation.images.up]" in names
    assert "video_span_matches_length[observation.images.side]" in names


def _corrupt_copy(src: Path, dst: Path) -> Path:
    shutil.copytree(src, dst)
    return dst


def test_frame_total_mismatch_is_caught(so101_root: Path, tmp_path: Path) -> None:
    root = _corrupt_copy(so101_root, tmp_path / "ds")
    info_path = root / "meta" / "info.json"
    info = json.loads(info_path.read_text())
    info["total_frames"] = 12000
    info_path.write_text(json.dumps(info))
    insp = inspect_root(root)
    failed = {c.name for c in insp.failed_checks}
    assert failed == {"frame_total_matches"}


def test_truncated_episode_fails_video_span_check(so101_root: Path, tmp_path: Path) -> None:
    root = _corrupt_copy(so101_root, tmp_path / "ds")
    path = root / "meta" / "episodes" / "chunk-000" / "file-000.parquet"
    episodes = pd.read_parquet(path)
    episodes.at[3, "length"] = int(episodes["length"].to_numpy()[3]) - 5  # span now too long
    episodes.to_parquet(path)
    insp = inspect_root(root)
    failed = {c.name for c in insp.failed_checks}
    assert "video_span_matches_length[observation.images.up]" in failed
    assert "frame_total_matches" in failed  # total_frames in info.json no longer matches


def test_length_outliers_use_robust_statistics(so101_root: Path, tmp_path: Path) -> None:
    root = _corrupt_copy(so101_root, tmp_path / "ds")
    path = root / "meta" / "episodes" / "chunk-000" / "file-000.parquet"
    episodes = pd.read_parquet(path)
    episodes.at[7, "length"] = 5000  # one absurdly long episode
    episodes.to_parquet(path)
    insp = inspect_root(root)
    assert insp.episode_lengths.long_outliers == [7]
    assert insp.episode_lengths.short_outliers == []
