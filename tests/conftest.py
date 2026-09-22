"""Shared fixtures: a real dataset's ``meta/`` recorded from the Hub on 2026-09-21."""

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def so101_root() -> Path:
    """Root of ``lerobot/svla_so101_pickplace`` metadata (50 episodes, 11939 frames, 30 fps)."""
    return FIXTURES / "svla_so101_pickplace"
