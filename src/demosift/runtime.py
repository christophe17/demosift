"""The AgentCore Runtime entrypoint.

AgentCore Runtime hosts a container that answers ``POST /invocations`` and ``GET /ping`` on
port 8080; the ``bedrock_agentcore`` SDK implements that contract and calls the function
decorated with ``@app.entrypoint`` with the request payload. Two modes:

- ``{"dataset_id": "...", "mode": "inspect"}`` runs the deterministic inspection only and
  returns it with its Markdown rendering. No model call, no cost beyond the download.
- ``{"dataset_id": "..."}`` (default mode ``agent``) also asks the agent for a narrative.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from bedrock_agentcore.runtime import BedrockAgentCoreApp

from demosift.agent import inspect_dataset_impl, run_inspection
from demosift.config import Settings
from demosift.inspection import Inspection
from demosift.report import to_markdown

MODES = ("inspect", "agent")

app = BedrockAgentCoreApp()
log = logging.getLogger("demosift.runtime")


def handle(payload: dict[str, Any]) -> dict[str, Any]:
    """Serve one request; pure function so it can be tested without the HTTP server."""
    dataset_id = payload.get("dataset_id")
    mode = payload.get("mode", "agent")
    if not isinstance(dataset_id, str) or not dataset_id.strip():
        return {"error": "payload must contain a non-empty string 'dataset_id'"}
    if mode not in MODES:
        return {"error": f"mode must be one of {MODES}"}

    started = time.perf_counter()
    settings = Settings.from_env()
    inspection_dict = inspect_dataset_impl(dataset_id, cache_dir=settings.hf_cache_dir)
    inspection = Inspection.model_validate(inspection_dict)
    response: dict[str, Any] = {
        "dataset_id": dataset_id,
        "mode": mode,
        "passed": inspection.passed,
        "inspection": inspection_dict,
        "markdown": to_markdown(inspection),
    }
    if mode == "agent":
        narrative, usage = run_inspection(dataset_id)
        response["narrative"] = narrative
        response["usage"] = usage
        response["model_id"] = settings.model_id
    response["latency_seconds"] = round(time.perf_counter() - started, 3)
    log.info(
        "inspected %s mode=%s passed=%s in %.2fs",
        dataset_id,
        mode,
        inspection.passed,
        response["latency_seconds"],
    )
    return response


@app.entrypoint
def invoke(payload: dict[str, Any], context: object | None = None) -> dict[str, Any]:  # noqa: ARG001
    """AgentCore Runtime entrypoint; ``context`` carries the session id and is unused so far."""
    return handle(payload)


def main() -> None:
    """Start the HTTP server the Runtime contract expects (port 8080)."""
    logging.basicConfig(level=Settings.from_env().log_level)
    app.run()


if __name__ == "__main__":
    main()
