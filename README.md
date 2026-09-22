# demosift

**Audit LeRobot datasets before you train on them.**

demosift reads a robot-demonstration dataset from the Hugging Face Hub, checks it, and writes
a quality report. It runs from a laptop as a command line, and as an agent on Amazon Bedrock
AgentCore. Today it performs the **level-0 inspection**: format, robot, cameras, tasks,
episode lengths and the consistency checks a broken upload fails. The next milestones add the
numeric audit of frames, the visual audit of sampled frames, and a gold set that measures the
audit itself. See [docs/02-milestones.md](docs/02-milestones.md).

**Live instance:** not deployed yet (milestone 0 in progress).

## Measured numbers

No number in this table is estimated: each comes from a recorded run in
[JOURNAL.md](JOURNAL.md), and the table is updated when the numbers change.

| Metric | Value | Recorded |
|---|---|---|
| Datasets audited on the public instance | not deployed yet | — |
| CLI wall clock, metadata cached | 1.6 s, of which 0.04 s is the inspection itself (`lerobot/svla_so100_stacking`, 56 episodes) | 2026-09-21 |
| CLI wall clock, metadata downloaded | 5.5 s, of which 2.1 s is the download of four files (same dataset, fresh cache) | 2026-09-21 |
| Runtime container, `inspect` mode, metadata downloaded | 1.83 s (`lerobot/svla_so101_pickplace`, local Docker, arm64) | 2026-09-21 |
| Runtime container, `inspect` mode, metadata cached | 0.14 s (same request repeated) | 2026-09-21 |
| Runtime image size | 590 MB (linux/arm64) | 2026-09-21 |
| Cost per inspection in `inspect` mode | 0 model tokens (deterministic) | 2026-09-21 |
| Cost per inspection in `agent` mode | not measured yet (no Bedrock call made so far) | — |
| Test suite | 20 tests, 90 % line coverage | 2026-09-21 |

## Quick start

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run demosift inspect lerobot/svla_so101_pickplace          # Markdown report
uv run demosift inspect --json lerobot/aloha_sim_insertion_human
uv run demosift inspect ./path/to/a/local/dataset             # any directory with meta/
```

The exit code is 0 when every check passes and 1 otherwise, so the command works in CI.
Only `meta/` is downloaded (a few hundred kilobytes); set `HF_TOKEN` for private datasets.

Agent mode asks a Bedrock model to narrate the inspection. It needs AWS credentials with
Bedrock access in `eu-central-1` (override with `DEMOSIFT_MODEL_ID` and `DEMOSIFT_REGION`):

```bash
uv run demosift agent lerobot/svla_so101_pickplace
```

The AgentCore Runtime server can run locally:

```bash
uv run demosift serve   # listens on :8080
curl -s -X POST localhost:8080/invocations -H 'content-type: application/json' \
  -d '{"dataset_id": "lerobot/svla_so101_pickplace", "mode": "inspect"}'
```

## What the level-0 inspection reports

- **Facts:** LeRobot codebase version, robot type, cameras with resolution, fps and codec,
  state and action dimensions with their names, tasks with episode and frame counts, episode
  length distribution (min, median, max, mean, std, total duration).
- **Consistency checks:** frame total matches `info.json`; episode count matches; episode
  indices are contiguous; fps is positive; no empty episode; every episode carries a task
  listed in `tasks.parquet`; for each camera, the video span of every episode matches its
  length within one frame.
- **Hints:** episodes whose length is a robust outlier (median absolute deviation, z beyond
  3.5) are listed as worth a look, never as a failure.

What it cannot see yet: timestamp gaps inside episodes, frozen frames, action ranges, and
the visual content of the videos. Those are milestones 1 and 2.

Only datasets in LeRobot codebase **v3.0** are read; older versions are refused with an
explicit error. The format as observed on real datasets is documented in
[docs/04-lerobot-dataset-format.md](docs/04-lerobot-dataset-format.md).

## Architecture

```
laptop ──── demosift CLI ───────────────┐
                                        ▼
AgentCore Runtime (container, :8080)  handle(payload)
   └─ Strands agent on Bedrock ──▶ tool inspect_dataset ──▶ Hub meta/ ──▶ Inspection ──▶ Markdown/JSON
```

The core is deterministic: every number in a report comes from the inspection code, never
from the model. The agent only narrates. Details, and the target multi-agent layout of the
later milestones, are in [docs/01-architecture.md](docs/01-architecture.md).

## Repository layout

```
src/demosift/        the package: format reader, Hub access, inspection, report, agent, runtime, CLI
tests/               pytest suite on a real dataset's recorded metadata (tests/fixtures/)
services/runtime/    Dockerfile of the AgentCore Runtime container (linux/arm64)
infra/               Terraform: modules/ and envs/dev/foundation (budget, ECR, Runtime)
docs/                architecture, milestones, decisions, dataset format, cost and security
CLAUDE.md            working rules of the repository; STATE.md and JOURNAL.md track progress
```

## Development

```bash
make install     # uv sync
make lint        # ruff check, ruff format --check, mypy --strict
make test        # pytest with coverage
make docker-build
make tf-check    # terraform fmt, validate, tflint, trivy
```

## Deployment

Infrastructure is Terraform only; see [infra/README.md](infra/README.md). The runtime image
is built for `linux/arm64`, which AgentCore Runtime requires.

## Contributing

Issues and pull requests are welcome. Ideas outside the current milestone go into an issue
first (see [docs/02-milestones.md](docs/02-milestones.md)); the repository's working rules
are in [CLAUDE.md](CLAUDE.md).

## License

Apache-2.0. See [LICENSE](LICENSE).
