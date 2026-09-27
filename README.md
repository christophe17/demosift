# demosift

**Audit LeRobot datasets before you train on them.**

demosift reads a robot-demonstration dataset from the Hugging Face Hub, checks it, and writes a
quality report. It is a **deterministic library and a command line**: no model, no agent, no
cloud account. Every number in a report comes from code you can read and test. Today it
performs the **level-0 inspection**: format, robot, cameras, tasks, episode lengths and the
consistency checks a broken upload fails. The next milestones add the frame-level numeric audit,
then the visual audit of sampled frames with its calibration. See
[docs/02-milestones.md](docs/02-milestones.md).

A hosted instance with a browser front end, sign-in and an assistant you can question about an
audit is being built at `demosift.io` (not open yet). It runs this package; it lives in its own
repository.

## Measured numbers

No number in this table is estimated: each comes from a recorded run in
[JOURNAL.md](JOURNAL.md), and the table is updated when the numbers change.

| Metric | Value | Recorded |
|---|---|---|
| CLI wall clock, metadata cached | 1.6 s, of which 0.04 s is the inspection itself (`lerobot/svla_so100_stacking`, 56 episodes) | 2026-09-21 |
| CLI wall clock, metadata downloaded | 5.5 s, of which 2.1 s is the download of four files (same dataset, fresh cache) | 2026-09-21 |
| Dependencies of a bare install | 40 packages in the lock file, none of them a cloud or agent SDK (was 139) | 2026-09-27 |
| Command-line image | 524 MB, `linux/amd64` and `linux/arm64` | 2026-09-27 |
| Test suite | 22 tests, 95 % line coverage | 2026-09-27 |

## Quick start

Requires Python 3.12. Until the package is on PyPI, install from the release tag:

```bash
pip install "demosift @ git+https://github.com/christophe17/demosift@v0.2.0"
demosift inspect lerobot/svla_so101_pickplace          # text on a terminal, Markdown when piped
demosift inspect --format markdown lerobot/svla_so101_pickplace > report.md
demosift inspect --json lerobot/aloha_sim_insertion_human
demosift inspect ./path/to/a/local/dataset             # any directory with meta/
```

On a terminal the report is coloured and fitted to the window; `NO_COLOR` turns the colour
off and `--format` fixes the rendering (`text`, `markdown` or `json`) wherever the output goes.
The exit code is 0 when every check passes and 1 otherwise, so the command works in CI.
Only `meta/` is downloaded (a few hundred kilobytes); set `HF_TOKEN` for private datasets.

Without Python, the same command line runs from the published image:

```bash
docker run --rm ghcr.io/christophe17/demosift:v0.2.0 inspect lerobot/svla_so101_pickplace
```

## As a library

Everything the command line does is a function call. The public surface is re-exported from
the package root, so nothing deeper needs importing:

```python
from demosift import inspect_root, resolve_source, to_markdown, to_text

root = resolve_source("lerobot/svla_so101_pickplace")   # downloads meta/ into the Hub cache
inspection = inspect_root(root, "lerobot/svla_so101_pickplace")
print(inspection.passed, [c.name for c in inspection.failed_checks])
print(to_markdown(inspection))                          # for a dataset card or a file
print(to_text(inspection, width=80, color=True))        # for a terminal
```

`Inspection` is a Pydantic model: `inspection.model_dump(mode="json")` is what a service stores
or returns. The surface and its stability rules are in
[docs/01-architecture.md](docs/01-architecture.md) §3.

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

## What this repository does not do

It calls no model, runs no agent, serves no HTTP, and deploys nothing. Those belong to the
hosted instance, which imports this package and adds an assistant, a queue, a database and the
infrastructure around them. Keeping them out is what makes the auditor testable to the last
digit and usable by anyone, on any machine, without an account anywhere.

## Repository layout

```
src/demosift/   the package: format reader, Hub access, inspection, report, CLI
tests/          pytest suite on a real dataset's recorded metadata (tests/fixtures/)
Dockerfile      the command line in a box
docs/           architecture, milestones, decisions, dataset format, bounds and robustness
CLAUDE.md       working rules of the repository; STATE.md and JOURNAL.md track progress
```

## Development

```bash
make install     # uv sync
make lint        # ruff check, ruff format --check, mypy --strict
make test        # pytest with coverage
make docker-build && make docker-run DATASET=lerobot/svla_so101_pickplace
```

## Contributing

Issues and pull requests are welcome. Ideas outside the current milestone go into an issue
first (see [docs/02-milestones.md](docs/02-milestones.md)); the repository's working rules
are in [CLAUDE.md](CLAUDE.md).

## License

Apache-2.0. See [LICENSE](LICENSE).
