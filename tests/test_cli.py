import json
import shutil
from pathlib import Path

import pytest
from click.testing import CliRunner

from demosift.cli import main


def test_inspect_command_prints_markdown_when_stdout_is_not_a_terminal(so101_root: Path) -> None:
    result = CliRunner().invoke(main, ["inspect", str(so101_root)])
    assert result.exit_code == 0, result.output
    assert "**Verdict:** all checks passed." in result.output


def test_inspect_command_json(so101_root: Path) -> None:
    result = CliRunner().invoke(main, ["inspect", "--json", str(so101_root)])
    assert result.exit_code == 0
    assert '"total_frames": 11939' in result.output
    explicit = CliRunner().invoke(main, ["inspect", "--format", "json", str(so101_root)])
    assert explicit.output == result.output


def test_inspect_format_text_is_plain_when_piped(so101_root: Path) -> None:
    result = CliRunner().invoke(main, ["inspect", "--format", "text", str(so101_root)], color=True)
    assert result.exit_code == 0, result.output
    assert result.output.splitlines()[0].endswith("  ✔ all checks passed")
    assert "\x1b" not in result.output
    markdown = CliRunner().invoke(main, ["inspect", "--format", "markdown", str(so101_root)])
    assert markdown.output.startswith("# Inspection of")


def test_inspect_on_a_terminal_defaults_to_coloured_text_unless_no_color(
    so101_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("demosift.cli._stdout_is_terminal", lambda: True)
    monkeypatch.delenv("NO_COLOR", raising=False)
    coloured = CliRunner().invoke(main, ["inspect", str(so101_root)], color=True).output
    assert "\x1b[32m" in coloured and "✔ all checks passed" in coloured
    monkeypatch.setenv("NO_COLOR", "1")
    plain = CliRunner().invoke(main, ["inspect", str(so101_root)], color=True).output
    assert "\x1b" not in plain and "✔ all checks passed" in plain


def test_inspect_exits_one_and_names_the_failure(so101_root: Path, tmp_path: Path) -> None:
    shutil.copytree(so101_root, tmp_path / "ds")
    info_path = tmp_path / "ds" / "meta" / "info.json"
    info = json.loads(info_path.read_text())
    info["total_episodes"] = 51
    info_path.write_text(json.dumps(info))
    result = CliRunner().invoke(main, ["inspect", "--format", "text", str(tmp_path / "ds")])
    assert result.exit_code == 1
    assert "✘ 1 check(s) failed" in result.output
    assert "  ✘ episode_count_matches: 50 episode rows, info.json declares 51" in result.output
