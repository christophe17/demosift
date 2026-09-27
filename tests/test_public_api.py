import sys
from pathlib import Path

import demosift


def test_public_surface_is_importable_from_the_package_root(so101_root: Path) -> None:
    inspection = demosift.inspect_root(so101_root, "lerobot/svla_so101_pickplace")
    assert inspection.passed
    assert demosift.to_markdown(inspection).startswith("# Inspection of")
    assert '"total_frames": 11939' in demosift.to_json(inspection)
    assert demosift.__version__


def test_nothing_in_the_package_imports_a_cloud_or_agent_library() -> None:
    forbidden = {"strands", "bedrock_agentcore", "boto3", "botocore", "opentelemetry"}
    loaded = {name.split(".")[0] for name in sys.modules}
    assert not (loaded & forbidden), sorted(loaded & forbidden)
