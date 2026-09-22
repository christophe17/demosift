# JOURNAL

Dated history. Every number quoted elsewhere in the repository points to an entry here.

## 2026-09-21 — Bootstrap of milestone 0

- Project created: `uv init --lib`, Python 3.12.9, dependencies resolved to
  `strands-agents 1.56.0`, `bedrock-agentcore 1.23.1`, `huggingface-hub 1.32.0`,
  `pandas 3.0.6`, `pyarrow 25.0.1`, `pydantic 2.13.5`, `click 8.5.0`.
- LeRobot format observed on the Hub for `lerobot/svla_so101_pickplace` and
  `lerobot/aloha_sim_insertion_human` (both `codebase_version v3.0`); the metadata of the
  first is recorded under `tests/fixtures/` (88 kB). Documented in
  `docs/04-lerobot-dataset-format.md`.
- Test suite: 20 tests pass, 90 % line coverage (`uv run pytest --cov`). `ruff check`,
  `ruff format --check` and `mypy --strict` clean.
- CLI run against live datasets not in the fixtures: `demosift inspect
  lerobot/aloha_sim_insertion_human` → 50 episodes, 25000 frames at 50 fps, one camera
  640x480 av1, 14-dim state and action without names, all checks pass.
  `lerobot/svla_so100_stacking` (56 episodes, 22956 frames) and `lerobot/svla_so100_sorting`
  (52 episodes, 35713 frames): all checks pass.
- Latency, laptop (Apple Silicon), `/usr/bin/time` on the CLI with a fresh cache directory:
  5.52 s wall clock with the download, 1.61 s with the metadata cached. In-process:
  `resolve_source` 2.11 s when downloading and 0.22 s when cached, `inspect_root` 0.014–0.044 s.
  The rest of the wall clock is Python start-up and imports.
- Runtime container built for linux/arm64 (590 MB) and run locally: `GET /ping` → Healthy;
  `POST /invocations` in `inspect` mode → 1.83 s with the download, 0.14 s repeated
  (`latency_seconds` in the response); an empty payload returns an explicit error.
- Runtime `agent` mode exercised in the tests with the agent stubbed. No Bedrock call made
  yet: no AWS account chosen for the project.
