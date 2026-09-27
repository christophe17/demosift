import json
import shutil
from pathlib import Path

import click
import pandas as pd

from demosift.inspection import inspect_root
from demosift.report import to_json, to_markdown, to_text


def test_markdown_carries_the_verdict_and_the_numbers(so101_root: Path) -> None:
    md = to_markdown(inspect_root(so101_root, "lerobot/svla_so101_pickplace"))
    assert md.startswith("# Inspection of `lerobot/svla_so101_pickplace`")
    assert "**Verdict:** all checks passed." in md
    assert "| Frames | 11939 at 30 fps (6 min 38.0 s) |" in md
    assert "| `observation.images.up` | 640x480x3 | 30 | av1 |" in md
    assert "| 0 | pink lego brick into the transparent box | 50 | 11939 |" in md
    assert "| `frame_total_matches` | pass |" in md


def test_json_round_trips(so101_root: Path) -> None:
    insp = inspect_root(so101_root)
    data = json.loads(to_json(insp))
    assert data["total_frames"] == 11939
    assert len(data["checks"]) == len(insp.checks)


def test_text_leads_with_the_verdict_and_fits_the_width(so101_root: Path) -> None:
    insp = inspect_root(so101_root, "lerobot/svla_so101_pickplace")
    text = to_text(insp, width=80)
    assert text.startswith("lerobot/svla_so101_pickplace  ✔ all checks passed\n")
    assert "Frames    11939 at 30 fps, 6 min 38.0 s" in text
    assert "Action    6 dims, same names as state" in text
    assert "observation.images.up    640x480x3   30   av1" in text
    assert "✔  frame_total_matches" in text
    assert "\x1b" not in text
    assert all(len(line) <= 80 for line in text.splitlines()), text
    assert to_text(insp, width=80) == text  # deterministic


def test_text_colour_only_adds_styles(so101_root: Path) -> None:
    insp = inspect_root(so101_root, "lerobot/svla_so101_pickplace")
    coloured = to_text(insp, color=True)
    assert "\x1b[32m" in coloured  # green
    assert click.unstyle(coloured) == to_text(insp)


def test_text_lists_failed_checks_under_the_verdict(so101_root: Path, tmp_path: Path) -> None:
    shutil.copytree(so101_root, tmp_path / "ds")
    info_path = tmp_path / "ds" / "meta" / "info.json"
    info = json.loads(info_path.read_text())
    info["total_frames"] = 12000
    info_path.write_text(json.dumps(info))
    lines = to_text(inspect_root(tmp_path / "ds"), color=True).splitlines()
    assert click.unstyle(lines[0]) == "ds  ✘ 1 check(s) failed"
    assert "\x1b[31m" in lines[0]  # red
    assert lines[1].startswith("  ✘ frame_total_matches: episode lengths sum to 11939")
    assert any(click.unstyle(line).startswith("✘  frame_total_matches") for line in lines)


def test_text_neutralises_control_characters_from_the_dataset(
    so101_root: Path, tmp_path: Path
) -> None:
    hostile = "pick the 箸 brick\x1b[2J\x07 quietly, vite\u0301"  # wide, control, combining
    root = tmp_path / "ds"
    shutil.copytree(so101_root, root)
    tasks_path = root / "meta" / "tasks.parquet"
    tasks = pd.read_parquet(tasks_path)
    tasks.index = pd.Index([hostile])
    tasks.to_parquet(tasks_path)
    episodes_path = root / "meta" / "episodes" / "chunk-000" / "file-000.parquet"
    episodes = pd.read_parquet(episodes_path)
    episodes["tasks"] = [[hostile]] * len(episodes)
    episodes.to_parquet(episodes_path)

    insp = inspect_root(root)
    assert insp.passed, [c.detail for c in insp.failed_checks]
    text = to_text(insp)
    assert "\x1b" not in text and "\x07" not in text
    assert "pick the 箸 brick?[2J? quietly, vite\u0301" in text
    assert hostile in to_markdown(insp)  # Markdown quotes the dataset verbatim, as data


def test_text_covers_the_optional_lines(so101_root: Path) -> None:
    insp = inspect_root(so101_root)
    lengths = insp.episode_lengths.model_copy(update={"long_outliers": [3]})
    sparse = insp.model_copy(
        update={"cameras": [], "state_names": None, "episode_lengths": lengths}
    )
    text = to_text(sparse)
    assert "No camera stream declared." in text
    assert "Length outliers (robust z beyond 3.5): short none, long [3]." in text
    assert "State     6 dims\n" in text
    assert "Action    6 dims: shoulder_pan.pos" in text
    narrow = to_text(sparse, width=10)  # raised to the minimum width, still renders
    assert all(len(line) <= 40 for line in narrow.splitlines()[1:]), narrow  # title excepted
    assert "video_span_matches_…" in narrow  # long cells are cut, the last column wraps
