"""The inspection agent: a Strands agent on Bedrock with one deterministic tool.

At this milestone the agent does one thing: call the inspection tool on the requested dataset
and write a short, faithful narrative of what the tool returned. Everything numeric comes
from the tool; the model never estimates a number. Later milestones add the numeric-audit,
visual-audit and report-writing agents around this one.
"""

from __future__ import annotations

from typing import Any

from strands import Agent, tool
from strands.models import BedrockModel

from demosift.config import Settings
from demosift.hub import resolve_source
from demosift.inspection import inspect_root

SYSTEM_PROMPT = """You are demosift, an auditor of LeRobot robot-demonstration datasets.

You have one tool, `inspect_dataset`, which reads a dataset's metadata and returns facts and
consistency checks. Rules:
- Always call the tool first; never guess a number, a camera name or a task text.
- Report only what the tool returned. Quote its numbers exactly.
- Start with the verdict (all checks passed, or which failed and what that means for training).
- Then summarize in at most eight short lines: robot, cameras and resolution, state/action
  dimensions, tasks with episode counts, episode length range and total duration.
- If lengths have outliers, name the episode indices and say they deserve a look.
- Say plainly what this level-0 inspection cannot see: frame-level timing, frozen frames,
  action ranges and the visual content of the videos are not checked yet.
Write in plain English, no marketing, no emojis."""


def inspect_dataset_impl(dataset_id: str, *, cache_dir: str | None = None) -> dict[str, Any]:
    """Run the level-0 inspection and return it as a JSON-compatible dict."""
    root = resolve_source(dataset_id, cache_dir=cache_dir)
    return inspect_root(root, dataset_id).model_dump(mode="json")


@tool
def inspect_dataset(dataset_id: str) -> dict[str, Any]:
    """Inspect a LeRobot dataset from the Hugging Face Hub and return facts and checks.

    Args:
        dataset_id: Hub identifier of the dataset, for example ``lerobot/svla_so101_pickplace``.

    Returns:
        The level-0 inspection: format version, robot type, cameras, state and action
        dimensions, tasks, episode-length statistics and the list of consistency checks with
        their pass/fail verdict.
    """
    return inspect_dataset_impl(dataset_id, cache_dir=Settings.from_env().hf_cache_dir)


def build_agent(settings: Settings | None = None) -> Agent:
    """Create the inspection agent on the configured Bedrock model."""
    settings = settings or Settings.from_env()
    model = BedrockModel(
        model_id=settings.model_id,
        region_name=settings.region,
        temperature=0.0,
        max_tokens=1500,
    )
    return Agent(
        model=model,
        tools=[inspect_dataset],
        system_prompt=SYSTEM_PROMPT,
        callback_handler=None,
    )


def usage_of(result: object) -> dict[str, int]:
    """Extract token usage from a Strands result, tolerating missing fields."""
    metrics = getattr(result, "metrics", None)
    usage = getattr(metrics, "accumulated_usage", None) or {}
    return {
        "input_tokens": int(usage.get("inputTokens", 0)),
        "output_tokens": int(usage.get("outputTokens", 0)),
    }


def run_inspection(dataset_id: str, *, agent: Agent | None = None) -> tuple[str, dict[str, int]]:
    """Ask the agent to inspect ``dataset_id``; return its narrative and the token usage."""
    agent = agent or build_agent()
    result = agent(f"Inspect the dataset `{dataset_id}`.")
    return str(result).strip(), usage_of(result)
