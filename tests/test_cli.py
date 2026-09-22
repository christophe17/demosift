from pathlib import Path

from click.testing import CliRunner

from demosift.cli import main


def test_inspect_command_prints_markdown_and_exits_zero(so101_root: Path) -> None:
    result = CliRunner().invoke(main, ["inspect", str(so101_root)])
    assert result.exit_code == 0, result.output
    assert "**Verdict:** all checks passed." in result.output


def test_inspect_command_json(so101_root: Path) -> None:
    result = CliRunner().invoke(main, ["inspect", "--json", str(so101_root)])
    assert result.exit_code == 0
    assert '"total_frames": 11939' in result.output
