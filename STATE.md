# STATE

**Current milestone: 0 — Foundation.** Started 2026-09-21. `v0.2.0` released 2026-09-27;
`v0.3.0` ready to tag.

## Done

- Repository bootstrapped: package, tests, lint and types clean, CLI validated on live Hub
  datasets, command-line image, CI workflow (lint, types, tests, image build, dependency audit,
  secret scan).
- Public repository created and pushed 2026-09-22:
  <https://github.com/christophe17/demosift> (personal account for now, D9).
- `v0.1.0` released 2026-09-25, when the package still carried an agent and a Runtime.
- **D18, 2026-09-27: the agent, the Runtime entrypoint and every cloud dependency removed.**
  The package is the deterministic auditor and its CLI; the public surface is
  `demosift/__init__.py`; 40 packages in the lock file, 14 tests, 93 % coverage. The
  `release` workflow now publishes a wheel and a GitHub release, PyPI when trusted publishing
  is configured, and the command-line image on GHCR.
- **D19, 2026-09-27: terminal rendering.** `to_text` on the public surface and `--format` on the
  CLI (text on a terminal, Markdown when piped); 22 tests, 95 % coverage. Committed 41 minutes
  after the `v0.2.0` tag, so it is not in that release; it ships in `v0.3.0`.
- **`v0.2.0` released 2026-09-27** on the D18 commit: wheel and sdist on the GitHub release,
  the CLI image on GHCR, PyPI skipped (`PYPI_PUBLISH` unset). `ci` on that commit was red:
  `ruff format --check` now formats the README's Python block and rejected its aligned
  comments; reformatted 2026-09-28, 22 tests green, version bumped to `0.3.0`.

## Next steps, in order

1. **Push the README reformat and the `0.3.0` bump (committed 2026-09-30), `ci` green on
   `main`; then tag `v0.3.0`** and push the tag; watch the `release` workflow (wheel, GitHub release, image).
   The hosted instance stays pinned to `v0.2.0` until it needs `to_text`.
2. **PyPI, once** *(author, optional now)*: create the project on PyPI with trusted publishing
   for this repository and the `pypi` environment, then set the repository variable
   `PYPI_PUBLISH=true`; the next tag publishes. Until then the install line uses the git tag.
3. **Learning guide** for milestone 0 (`docs/guides/00-foundation.md`): the format, the
   checks, the public surface, the release pipeline, written against what exists.
4. **Milestone 1 opens**: the numeric audit (`docs/02`), starting with the bounds of `docs/05`
   §1 so that the first frame-level reader is born bounded.

Milestone 0 closes when steps 1 and 3 are done.

## Numbers

See the table in `README.md`; the latencies date from 2026-09-21 on a laptop, the footprint and
coverage from 2026-09-27.

## Pending decisions

- **GitHub organization name** (`docs/03-decisions.md` D9). A repository moves to an
  organization later without losing its history or breaking its links.
- **The `VisionJudge` protocol's exact shape** (`docs/01` §4): decided when milestone 2 opens,
  with the first real judge in hand.
