"""Command-line interface over the library."""

from __future__ import annotations

import os
import shutil
import sys

import click

from demosift.config import Settings
from demosift.hub import resolve_source
from demosift.inspection import Inspection, inspect_root
from demosift.report import TEXT_WIDTH, to_json, to_markdown, to_text

FORMATS = ("text", "markdown", "json")
MAX_TEXT_WIDTH = 160


def _stdout_is_terminal() -> bool:
    return sys.stdout.isatty()


def _render(inspection: Inspection, fmt: str | None) -> str:
    """Render in ``fmt``; when none is asked, text on a terminal and Markdown when piped.

    Colour follows the terminal too, and the ``NO_COLOR`` convention turns it off.
    """
    terminal = _stdout_is_terminal()
    fmt = fmt or ("text" if terminal else "markdown")
    if fmt == "json":
        return to_json(inspection)
    if fmt == "markdown":
        return to_markdown(inspection)
    width = min(shutil.get_terminal_size((TEXT_WIDTH, 24)).columns, MAX_TEXT_WIDTH)
    color = terminal and not os.environ.get("NO_COLOR")
    return to_text(inspection, width=width, color=color)


@click.group()
@click.version_option(package_name="demosift")
def main() -> None:
    """Audit LeRobot datasets from the command line."""


@main.command()
@click.argument("dataset")
@click.option(
    "--format",
    "fmt",
    type=click.Choice(FORMATS),
    default=None,
    help="Output format. Default: text on a terminal, Markdown when piped or redirected.",
)
@click.option("--json", "as_json", is_flag=True, help="Same as --format json.")
@click.option("--cache-dir", default=None, help="Where to store downloaded metadata.")
def inspect(dataset: str, fmt: str | None, as_json: bool, cache_dir: str | None) -> None:
    """Run the deterministic level-0 inspection of DATASET (a Hub id or a local directory)."""
    root = resolve_source(dataset, cache_dir=cache_dir or Settings.from_env().hf_cache_dir)
    inspection = inspect_root(root, dataset)
    click.echo(_render(inspection, "json" if as_json else fmt))
    sys.exit(0 if inspection.passed else 1)
