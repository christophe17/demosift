import json
from pathlib import Path

from demosift.inspection import inspect_root
from demosift.report import to_json, to_markdown


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
