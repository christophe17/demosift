"""Command-line interface over the library."""

from __future__ import annotations

import sys

import click

from demosift.config import Settings
from demosift.hub import resolve_source
from demosift.inspection import inspect_root
from demosift.report import to_json, to_markdown


@click.group()
@click.version_option(package_name="demosift")
def main() -> None:
    """Audit LeRobot datasets from the command line."""


@main.command()
@click.argument("dataset")
@click.option("--json", "as_json", is_flag=True, help="Print JSON instead of Markdown.")
@click.option("--cache-dir", default=None, help="Where to store downloaded metadata.")
def inspect(dataset: str, as_json: bool, cache_dir: str | None) -> None:
    """Run the deterministic level-0 inspection of DATASET (a Hub id or a local directory)."""
    root = resolve_source(dataset, cache_dir=cache_dir or Settings.from_env().hf_cache_dir)
    inspection = inspect_root(root, dataset)
    click.echo(to_json(inspection) if as_json else to_markdown(inspection))
    sys.exit(0 if inspection.passed else 1)
