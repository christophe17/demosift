import json
from pathlib import Path

import pytest

from demosift.format import UnsupportedFormatError, load_meta, read_info


def test_info_is_parsed_with_real_values(so101_root: Path) -> None:
    info = read_info(so101_root)
    assert info.codebase_version == "v3.0"
    assert info.robot_type == "so100_follower"
    assert (info.total_episodes, info.total_frames, info.fps) == (50, 11939, 30)
    assert info.camera_keys == ["observation.images.up", "observation.images.side"]
    assert info.vector_dim("action") == 6
    assert info.features["action"].flat_names == [
        "shoulder_pan.pos",
        "shoulder_lift.pos",
        "elbow_flex.pos",
        "wrist_flex.pos",
        "wrist_roll.pos",
        "gripper.pos",
    ]
    assert info.features["observation.images.up"].video_info is not None
    assert info.features["observation.images.up"].video_info["video.codec"] == "av1"


def test_meta_tables_have_expected_shapes(so101_root: Path) -> None:
    meta = load_meta(so101_root)
    assert len(meta.episodes) == 50
    assert list(meta.episodes["episode_index"]) == list(range(50))
    assert int(meta.episodes["length"].sum()) == 11939
    assert meta.task_texts == {0: "pink lego brick into the transparent box"}
    assert meta.stats is not None
    assert set(meta.stats["action"]) == {"min", "max", "mean", "std", "count"}


def test_unsupported_version_is_refused(tmp_path: Path, so101_root: Path) -> None:
    meta_dir = tmp_path / "meta"
    meta_dir.mkdir()
    info = json.loads((so101_root / "meta" / "info.json").read_text())
    info["codebase_version"] = "v2.1"
    (meta_dir / "info.json").write_text(json.dumps(info))
    with pytest.raises(UnsupportedFormatError, match=r"v2\.1"):
        read_info(tmp_path)
