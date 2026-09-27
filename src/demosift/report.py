"""Rendering an inspection as Markdown, plain text or JSON.

Markdown is for dataset cards and files, plain text for a terminal, JSON for tools. Every
renderer is a pure function from an ``Inspection`` to a string; the CLI picks one and prints it.
The text renderer replaces control characters in anything that comes from the dataset, so a
hostile task text cannot drive the terminal; the other two quote the dataset verbatim, as data.
"""

from __future__ import annotations

import textwrap
import unicodedata

import click

from demosift.inspection import EpisodeLengths, Inspection

OUTLIER_NOTE = "Worth a look, not a failure."
TICK = "✔"
CROSS = "✘"
RULE = "─"
GAP = "  "
TEXT_WIDTH = 100
MIN_TEXT_WIDTH = 40
MIN_LAST_COLUMN = 12


def _fmt_seconds(seconds: float) -> str:
    minutes, rest = divmod(seconds, 60)
    return f"{int(minutes)} min {rest:04.1f} s" if minutes else f"{rest:.1f} s"


def _vector(dim: int | None, names: list[str] | None) -> str:
    text = f"{dim} dims" if dim is not None else "absent"
    if names:
        text += ": " + ", ".join(names)
    return text


def _lengths_summary(el: EpisodeLengths) -> list[str]:
    lines = [
        (
            f"{el.count} episodes; min {el.min}, median {el.median:g}, max {el.max} frames "
            f"(mean {el.mean:.1f}, std {el.std:.1f}); {_fmt_seconds(el.total_seconds)} in total."
        )
    ]
    if el.short_outliers or el.long_outliers:
        lines.append(
            f"Length outliers (robust z beyond 3.5): short {el.short_outliers or 'none'}, "
            f"long {el.long_outliers or 'none'}. {OUTLIER_NOTE}"
        )
    return lines


# --------------------------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------------------------


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
    return ["## Episode lengths", "", *_lengths_summary(inspection.episode_lengths)]


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


# --------------------------------------------------------------------------------------------
# Plain text for a terminal
# --------------------------------------------------------------------------------------------


class _Paint:
    """``click.style`` when colour is on, the identity otherwise."""

    def __init__(self, color: bool) -> None:
        self.on = color

    def __call__(self, text: str, *, fg: str | None = None, bold: bool = False) -> str:
        return click.style(text, fg=fg, bold=bold) if self.on and text else text


def _clean(text: str) -> str:
    """Replace every character a terminal could act on (control codes) with ``?``."""
    return "".join(ch if ch.isprintable() else "?" for ch in text)


def _display_width(text: str) -> int:
    """Columns ``text`` occupies: wide East Asian characters take two, combining marks none."""
    width = 0
    for ch in click.unstyle(text):
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in {"W", "F"} else 1
    return width


def _truncate(text: str, max_width: int) -> str:
    if _display_width(text) <= max_width:
        return text
    kept, used = [], 0
    for ch in click.unstyle(text):
        used += _display_width(ch)
        if used > max_width - 1:
            break
        kept.append(ch)
    return "".join(kept) + "…"


def _pad(cell: str, width: int) -> str:
    return cell + " " * max(0, width - _display_width(cell))


def _table(
    headers: list[str],
    rows: list[list[str]],
    *,
    width: int,
    paint: _Paint,
    marks: bool = False,
) -> list[str]:
    """Aligned columns under a rule; the last column wraps, the others are capped at half.

    With ``marks``, the first column holds a pass or fail mark and is coloured accordingly.
    """
    cap = max(8, width // 2)
    rows = [[_truncate(_clean(c), cap) for c in row[:-1]] + [_clean(row[-1])] for row in rows]
    columns = list(zip(headers, *rows, strict=True))
    widths = [max(_display_width(cell) for cell in column) for column in columns]
    fixed = sum(widths[:-1]) + len(GAP) * (len(widths) - 1)
    widths[-1] = max(MIN_LAST_COLUMN, min(widths[-1], width - fixed))

    def styled(index: int, cell: str) -> str:
        if marks and index == 0:
            return paint(cell, fg="green" if cell == TICK else "red")
        return cell

    lines = [GAP.join(_pad(paint(h, bold=True), w) for h, w in zip(headers, widths, strict=True))]
    lines.append(GAP.join(RULE * w for w in widths))
    for row in rows:
        wrapped = textwrap.wrap(row[-1], widths[-1]) or [""]
        cells = [*row[:-1], wrapped[0]]
        lines.append(
            GAP.join(
                _pad(styled(i, c), w) for i, (c, w) in enumerate(zip(cells, widths, strict=True))
            )
        )
        lines.extend(" " * fixed + rest for rest in wrapped[1:])
    return [line.rstrip() for line in lines]


def _text_verdict(inspection: Inspection, *, width: int, paint: _Paint) -> list[str]:
    if inspection.passed:
        verdict = paint(f"{TICK} all checks passed", fg="green", bold=True)
    else:
        count = len(inspection.failed_checks)
        verdict = paint(f"{CROSS} {count} check(s) failed", fg="red", bold=True)
    lines = [f"{paint(_clean(inspection.dataset_id), bold=True)}{GAP}{verdict}"]
    for check in inspection.failed_checks:
        lines += textwrap.wrap(
            _clean(f"{check.name}: {check.detail}"),
            width,
            initial_indent=f"{GAP}{CROSS} ",
            subsequent_indent=" " * (len(GAP) + 2),
        )
    return lines


def _text_overview(inspection: Inspection, *, width: int, paint: _Paint) -> list[str]:
    same = bool(inspection.action_names) and inspection.action_names == inspection.state_names
    action = (
        f"{inspection.action_dim} dims, same names as state"
        if same
        else _vector(inspection.action_dim, inspection.action_names)
    )
    rows = [
        ["Format", f"LeRobot codebase {inspection.codebase_version}"],
        ["Robot", inspection.robot_type or "not declared"],
        ["Episodes", str(inspection.total_episodes)],
        [
            "Frames",
            (
                f"{inspection.total_frames} at {inspection.fps:g} fps, "
                f"{_fmt_seconds(inspection.duration_seconds)}"
            ),
        ],
        ["State", _vector(inspection.state_dim, inspection.state_names)],
        ["Action", action],
    ]
    table = _table(["Field", "Value"], rows, width=width, paint=paint)
    return [paint("Overview", bold=True), *table]


def _text_cameras(inspection: Inspection, *, width: int, paint: _Paint) -> list[str]:
    title = paint("Cameras", bold=True)
    if not inspection.cameras:
        return [title, "No camera stream declared."]
    rows = [
        [
            c.key,
            f"{c.width or '?'}x{c.height or '?'}x{c.channels or '?'}",
            f"{c.fps:g}" if c.fps is not None else "?",
            c.codec or "?",
        ]
        for c in inspection.cameras
    ]
    return [title, *_table(["Key", "Resolution", "fps", "Codec"], rows, width=width, paint=paint)]


def _text_tasks(inspection: Inspection, *, width: int, paint: _Paint) -> list[str]:
    rows = [[str(t.task_index), str(t.episodes), str(t.frames), t.text] for t in inspection.tasks]
    headers = ["#", "Episodes", "Frames", "Task"]
    return [paint("Tasks", bold=True), *_table(headers, rows, width=width, paint=paint)]


def _text_lengths(inspection: Inspection, *, width: int, paint: _Paint) -> list[str]:
    lines = [paint("Episode lengths", bold=True)]
    for sentence in _lengths_summary(inspection.episode_lengths):
        lines += textwrap.wrap(sentence, width)
    return lines


def _text_checks(inspection: Inspection, *, width: int, paint: _Paint) -> list[str]:
    rows = [[TICK if c.passed else CROSS, c.name, c.detail] for c in inspection.checks]
    table = _table(["", "Check", "Detail"], rows, width=width, paint=paint, marks=True)
    return [paint("Consistency checks", bold=True), *table]


def to_text(inspection: Inspection, *, width: int = TEXT_WIDTH, color: bool = False) -> str:
    """Render the inspection as plain text for a terminal.

    The verdict comes first and the failed checks right under it; then the sections of the
    Markdown card, in aligned columns, the last column of each table wrapped to ``width``.
    Strings that come from the dataset have their control characters replaced.

    Args:
        inspection: The inspection to render.
        width: Columns available; values under 40 are raised to 40.
        color: Emit ANSI styles (bold, green, red). Off by default, so a caller writing to a
            file gets plain text; the CLI turns it on when stdout is a terminal.
    """
    width = max(width, MIN_TEXT_WIDTH)
    paint = _Paint(color)
    sections = [
        _text_verdict(inspection, width=width, paint=paint),
        _text_overview(inspection, width=width, paint=paint),
        _text_cameras(inspection, width=width, paint=paint),
        _text_tasks(inspection, width=width, paint=paint),
        _text_lengths(inspection, width=width, paint=paint),
        _text_checks(inspection, width=width, paint=paint),
    ]
    return "\n\n".join("\n".join(section) for section in sections) + "\n"


def to_json(inspection: Inspection) -> str:
    """Render the inspection as indented JSON."""
    return inspection.model_dump_json(indent=2)
