from pathlib import Path

import pytest

from demosift import agent as agent_module
from demosift import runtime


def test_tool_impl_accepts_a_local_directory(so101_root: Path) -> None:
    data = agent_module.inspect_dataset_impl(str(so101_root))
    assert data["total_episodes"] == 50
    assert all(check["passed"] for check in data["checks"])


def test_tool_is_registered_with_its_docstring() -> None:
    spec = agent_module.inspect_dataset.tool_spec
    assert spec["name"] == "inspect_dataset"
    assert "dataset_id" in spec["inputSchema"]["json"]["properties"]


def test_runtime_inspect_mode_needs_no_model(so101_root: Path) -> None:
    response = runtime.handle({"dataset_id": str(so101_root), "mode": "inspect"})
    assert response["passed"] is True
    assert response["inspection"]["total_frames"] == 11939
    assert response["markdown"].startswith("# Inspection of")
    assert "narrative" not in response
    assert response["latency_seconds"] >= 0


def test_runtime_agent_mode_calls_the_agent(
    so101_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def fake_run(dataset_id: str) -> tuple[str, dict[str, int]]:
        calls.append(dataset_id)
        return "narrative", {"input_tokens": 10, "output_tokens": 5}

    monkeypatch.setattr(runtime, "run_inspection", fake_run)
    response = runtime.handle({"dataset_id": str(so101_root)})
    assert calls == [str(so101_root)]
    assert response["narrative"] == "narrative"
    assert response["usage"] == {"input_tokens": 10, "output_tokens": 5}


@pytest.mark.parametrize("payload", [{}, {"dataset_id": ""}, {"dataset_id": "x", "mode": "bogus"}])
def test_runtime_rejects_bad_payloads(payload: dict[str, str]) -> None:
    assert "error" in runtime.handle(payload)


def test_usage_extraction_tolerates_missing_metrics() -> None:
    assert agent_module.usage_of(object()) == {"input_tokens": 0, "output_tokens": 0}
