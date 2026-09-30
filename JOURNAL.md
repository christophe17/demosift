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

## 2026-09-22 — First push and first CI run

- Public repository created under the author's account (D9): <https://github.com/christophe17/demosift>.
- First CI run on `main`: `lint, types, tests`, `runtime image builds (linux/arm64)`, `dependency
  vulnerabilities` and `secret detection` green; `terraform fmt, validate, tflint` red. Cause: CI
  pinned Terraform 1.15.0, whose `validate` checks the required arguments of the `backend` block
  even with `init -backend=false`; our `backend "s3" {}` is partial by design (`backend.hcl`). The
  check was removed in 1.15.1 (hashicorp/terraform #38466). Reproduced offline with the 1.15.0
  binary; 1.15.8 passes. Fix: CI pinned to 1.15.8 and `required_version` raised to `>= 1.15.1`
  in the root and the two modules, so 1.15.0 is refused with an explicit message instead of a
  confusing validate error.

## 2026-09-23 — The public instance becomes its own repository

- Decided D12 and D13: the web service is a separate repository, `demosift-web`, created and
  specified the same day at `~/Sites/demosift-web`; the product name stays `demosift` on both
  sides; `demosift.io` is canonical. This repository keeps the library, the CLI, the agent,
  the Runtime container and the Terraform that deploys that Runtime.
- Consequences propagated: the Runtime is IAM-only and never sees an end-user token; sign-in,
  quota, history and the anonymous tier are the public instance's; Identity here means the
  outbound grant vault, Memory means conversational context, not records.
- `docs/01` gained Policy in the AgentCore table, the explicit exclusion of Browser, and the
  open question on Code Interpreter versus a Lambda for the fixed numeric audit.
- `STATE.md` reordered into numbered steps with the two decisions that block them.
- No code changed; nothing deployed.

## 2026-09-25 — Account chosen

- D14: the existing standalone account. Checked from the CLI: not a member of any
  organization; default region `eu-west-3`, hence the `--region` note in `STATE.md`; operator
  identity an IAM user with static keys, to keep with MFA and replace with Identity Center
  only if a second account appears. Nothing deployed yet.

## 2026-09-25 — The infrastructure leaves; the container contract stays

- D15: `infra/`, `.tflint.hcl`, the Terraform CI job and the `tf-*` Makefile targets moved to
  `demosift-web`, which now deploys the Runtime from this repository's image. Nothing else
  changed in the code; the image and its tests are untouched.
- D16: the fixed audits are Lambdas; Code Interpreter only for improvised code.
- `docs/01` gained §4 "Execution units" and §5 "The container contract"; `STATE.md` shrank to
  the five steps that are this repository's.
- D17, later the same day: `aws-opentelemetry-distro` added, the container runs under
  `opentelemetry-instrument` with `/ping` excluded, a `release` workflow publishes the image
  to GHCR on `v*` tags. Verified locally: the instrumented image still serves `/ping` and an
  `inspect` invocation: 1.47 s with the metadata download, `/ping` healthy, zero error-like log lines with the exporter disabled; `/ping` healthy with it enabled and no collector present.

## 2026-09-25 — v0.1.0 released

- Tag `v0.1.0` pushed on commit `abdc090`; the `release` workflow built the `linux/arm64` image
  under QEMU and published `ghcr.io/christophe17/demosift:v0.1.0` and `:sha-abdc090b8c14`
  in 121s (digest `sha256:01733a3eb6be93d561aec80b7eba05e8c8d6a3bc0463925ea78cfe606f11c3c6`). `ci` green on the same commit.
- Package visibility at publication: not readable from the laptop (the `gh` token lacks the
  `read:packages` scope); GHCR packages are private by default. Making it public is the one manual step (D17);
  until then the deployment's promotion needs a token with `read:packages`.

## 2026-09-27 — The agent leaves; the library stands alone (D18)

- Removed `agent.py`, `runtime.py`, their tests, `strands-agents`, `bedrock-agentcore` and
  `aws-opentelemetry-distro`. Added `demosift/__init__.py` as the public surface and a test
  that no cloud or agent module is ever imported by the package.
- Lock file: 139 packages to 40; none of them a cloud or agent SDK. Tests: 14, 93 % line
  coverage. `ruff` and `mypy --strict` clean.
- The Dockerfile is now the command line in a box (`ENTRYPOINT demosift`): built for the native
  architecture in 524 MB (was 590 MB); `inspect lerobot/aloha_sim_insertion_human` from the
  image passes all checks. CI builds it for `linux/amd64` and `linux/arm64`.
- `release` workflow rewritten: `uv build` and a GitHub release with the wheel and sdist
  attached; a `pypi` job behind the `PYPI_PUBLISH` variable using trusted publishing; the image
  to GHCR under the version and the short SHA.
- `docs/05` renamed to `05-bounds-and-robustness.md`: the library has no cost to bound and no
  secret to keep; what it has is hostile input.
- Version bumped to `0.2.0` (the removal is a breaking change); not tagged yet.

## 2026-09-27 — Terminal rendering (D19)

- `to_text` added to `report.py` and to the public surface: verdict first, failed checks under
  it, aligned columns, the last column wrapped to the width, colour through `click.style`,
  control characters from the dataset replaced (`docs/05`). Markdown and JSON unchanged.
- CLI: `--format text|markdown|json`; the default is text on a terminal and Markdown when
  piped, `--json` kept as an alias, `NO_COLOR` honoured, the width read from the terminal and
  capped at 160 columns.
- Rich tried on the existing Markdown and not adopted (D19): four more packages for an output
  that centred the title, padded every line and truncated the check names.
- Numbers: `report.py` 103 → 317 lines, `cli.py` 30 → 62; tests 14 → 22, line coverage
  93 % → 95 %; `ruff` and `mypy --strict` clean. Live on `lerobot/svla_so101_pickplace`: Markdown
  when piped, bold and green text on a pseudo-terminal, exit code 0. The image rebuilt at
  524 MB (unchanged): Markdown without `-t`, coloured text with it.
- Version stays `0.2.0`, still untagged: the addition ships in the tag.

## 2026-09-28 — The tag preceded D19; `ci` red on `main`

- `v0.2.0` was tagged and pushed on the D18 commit (`4c9d410`) at 11:19 on 2026-09-27; the
  `release` workflow published the wheel, the sdist and the CLI image, and skipped PyPI. D19 was
  committed at 12:00 the same day with the words "still untagged", which was wrong: the release
  holds D18 only, `to_text` and `--format` are unreleased. They ship in `v0.3.0`; the version is
  bumped, the README's install lines follow, the tag is the next step. Moving a published tag was
  not considered: the hosted instance's lock file records the commit `v0.2.0` resolved to.
- `ci` on the tagged commit failed at `ruff format --check`: the pinned ruff formats the Python
  block of `README.md` and rejected the aligned trailing comments. The three lines reformatted
  as ruff wants them; 22 files formatted, 22 tests green. The Markdown code blocks in `docs/`
  were unaffected.
