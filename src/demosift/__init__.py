"""demosift: audit LeRobot robot-demonstration datasets before you train on them.

A deterministic library and a command line. No model, no agent, no cloud: every number a
report contains comes from code you can read and test. The public surface is re-exported here
so that a deployment, or anyone else, imports from ``demosift`` and nothing deeper.
"""

from importlib.metadata import version

from demosift.format import DatasetMeta, UnsupportedFormatError, load_meta
from demosift.hub import fetch_meta, resolve_source
from demosift.inspection import Check, Inspection, inspect_meta, inspect_root
from demosift.report import to_json, to_markdown

__version__ = version("demosift")

__all__ = [
    "Check",
    "DatasetMeta",
    "Inspection",
    "UnsupportedFormatError",
    "__version__",
    "fetch_meta",
    "inspect_meta",
    "inspect_root",
    "load_meta",
    "resolve_source",
    "to_json",
    "to_markdown",
]
