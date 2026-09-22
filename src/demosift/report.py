"""Rendering an inspection as Markdown (for humans and dataset cards) or JSON (for tools)."""

from __future__ import annotations

from demosift.inspection import Inspection

OUTLIER_NOTE = "Worth a look, not a failure."


def _fmt_seconds(seconds: float) -> str:
    minutes, rest = divmod(seconds, 60)
    return f"{int(minutes)} min {rest:04.1f} s" if minutes else f"{rest:.1f} s"


def _vector(dim: int | None, names: list[str] | None) -> str:
    text = f"{dim} dims" if dim is not None else "absent"
    if names:
        text += ": " + ", ".join(names)
    return text


def _overview(inspection: Inspection) -> list[str]:
    frames = (
        f"{inspection.total_frames} at {inspection.fps:g} fps "
        f"({_fmt_seconds(inspection.duration_seconds)})"
    )
    rows = [
        ("Format", f"LeRobot codebase {inspection.codebase_version}"),
        ("Robot", inspection.robot_type or "not declared"),
        ("Episodes", str(inspection.total_episodes)),
        ("Frames", frames),
        ("State", _vector(inspection.state_dim, inspection.state_names)),
        ("Action", _vector(inspection.action_dim, inspection.action_names)),
    ]
    return ["## Overview", "", "| Field | Value |", "|---|---|"] + [
        f"| {field} | {value} |" for field, value in rows
    ]


def _cameras(inspection: Inspection) -> list[str]:
    lines = ["## Cameras", ""]
    if not inspection.cameras:
        return [*lines, "No camera stream declared."]
    lines += ["| Key | Resolution | fps | Codec |", "|---|---|---|---|"]
    for c in inspection.cameras:
        resolution = f"{c.width}x{c.height}x{c.channels}"
        fps = f"{c.fps:g}" if c.fps is not None else "?"
        lines.append(f"| `{c.key}` | {resolution} | {fps} | {c.codec or '?'} |")
    return lines


def _tasks(inspection: Inspection) -> list[str]:
    lines = ["## Tasks", "", "| # | Task | Episodes | Frames |", "|---|---|---|---|"]
    lines += [
        f"| {t.task_index} | {t.text} | {t.episodes} | {t.frames} |" for t in inspection.tasks
    ]
    return lines


def _lengths(inspection: Inspection) -> list[str]:
    el = inspection.episode_lengths
    summary = (
        f"{el.count} episodes; min {el.min}, median {el.median:g}, max {el.max} frames "
        f"(mean {el.mean:.1f}, std {el.std:.1f}); {_fmt_seconds(el.total_seconds)} in total."
    )
    lines = ["## Episode lengths", "", summary]
    if el.short_outliers or el.long_outliers:
        lines.append(
            f"Length outliers (robust z beyond 3.5): short {el.short_outliers or 'none'}, "
            f"long {el.long_outliers or 'none'}. {OUTLIER_NOTE}"
        )
    return lines


def _checks(inspection: Inspection) -> list[str]:
    lines = ["## Consistency checks", "", "| Check | Result | Detail |", "|---|---|---|"]
    lines.extend(
        f"| `{c.name}` | {'pass' if c.passed else 'FAIL'} | {c.detail} |" for c in inspection.checks
    )
    return lines


def to_markdown(inspection: Inspection) -> str:
    """Render the inspection as a Markdown card."""
    verdict = (
        "all checks passed"
        if inspection.passed
        else f"{len(inspection.failed_checks)} check(s) failed"
    )
    sections = [
        [f"# Inspection of `{inspection.dataset_id}`", "", f"**Verdict:** {verdict}."],
        _overview(inspection),
        _cameras(inspection),
        _tasks(inspection),
        _lengths(inspection),
        _checks(inspection),
    ]
    return "\n\n".join("\n".join(section) for section in sections) + "\n"


def to_json(inspection: Inspection) -> str:
    """Render the inspection as indented JSON."""
    return inspection.model_dump_json(indent=2)
