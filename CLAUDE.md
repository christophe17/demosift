# CLAUDE.md — demosift

Read first. This file gives the context, the non-negotiable rules and the reading order.

## 1. The project in one sentence

A multi-agent auditor of LeRobot robot-demonstration datasets: a user gives a Hugging Face
Hub dataset id, the system audits it and writes a quality report, from a laptop or as an
agent on Amazon Bedrock AgentCore (Runtime today; Gateway, Identity, Memory and Code
Interpreter in later milestones).

## 2. Context

- **Public repository, real users.** The users are the LeRobot community; the tool must be
  useful to them for free, and honest about what it can and cannot see.
- **Everything is in English**: code, comments, docs, commit messages, issues.
- **The author learns by reading.** Claude Code writes the code and, for each milestone, the
  guide that explains it (`docs/`). A milestone without its guide and its numbers is not done.
- **Bought conventions.** Quality rules, Terraform layout and CI shape are inherited from the
  author's earlier project (`cgp-ai`); the domain is new.

## 3. Reading order

1. `docs/01-architecture.md` — components, AgentCore mapping, request flow, target layout
2. `docs/02-milestones.md` — milestones, definition of done, what is excluded
3. `docs/03-decisions.md` — decision log
4. `docs/04-lerobot-dataset-format.md` — the v3.0 format as observed, and what each check verifies
5. `docs/05-cost-and-security.md` — guardrails before exposure, cost model, threat sketch
6. `infra/README.md` — Terraform layout and workflow

**Session resume:** read `CLAUDE.md`, `STATE.md` (current milestone, numbers, pending
decisions) and `JOURNAL.md` (dated history) before answering.

## 4. Non-negotiable rules

1. **No number from a model.** Every fact in a report — counts, durations, resolutions,
   verdicts — comes from deterministic code. The model narrates and never estimates.
2. **No number in a document without a run.** A figure in `README.md` or `docs/` cites the
   `JOURNAL.md` entry that produced it. "Not measured yet" is an acceptable value; a guess is
   not.
3. **Guardrails before exposure.** Nothing reachable from the Internet calls Bedrock without
   authentication, a per-user quota and a budget alarm (`docs/05-cost-and-security.md`).
4. **No secrets in the repository.** Tokens and credentials come from the environment or
   AWS-managed stores; `.gitignore` and the secrets scan in CI enforce it.
5. **Scope guard.** Work only on the current milestone (`STATE.md`). An idea outside it becomes
   an issue, not a change.
6. **Format honesty.** Only LeRobot codebase v3.0 is read; other versions are refused with an
   explicit error, never guessed at.
7. **Infrastructure only through Terraform.** No resource created by hand in the console;
   `apply` locally to `dev` only.
8. **Production quality from the first commit**: typed (`mypy --strict`), linted (`ruff`),
   tested (`pytest`, real recorded fixtures), no `TODO`, structured logs without tokens or
   personal data, explicit errors, timeouts and retries where a network is involved.
9. **Writing into a user's dataset card** (later milestone) happens only with that user's
   OAuth consent, on their own datasets, with a diff they can see.
10. **No conclusion from a single run.** Any metric about a model output is published from
    N runs with an interval; overlapping intervals are reported as "not significant".
11. **A verdict is published only once calibrated.** A visual-audit criterion becomes a
    verdict when its agreement with the gold set is measured (`docs/02-milestones.md`,
    "How the audit proves itself"); before that it is labelled indicative.
12. **Security is measured, not asserted.** Every control has a fixture attack replayed
    against it, with its block rate recorded (`docs/05-cost-and-security.md` §4).

## 5. Stack

Python 3.12, `uv`, `src/` layout, single package `demosift`. `pydantic` models, `pandas` +
`pyarrow` for parquet, `huggingface_hub` for the Hub, `strands-agents` for the agent,
`bedrock-agentcore` SDK for the Runtime contract, `click` for the CLI. Terraform ≥ 1.15 with
`hashicorp/aws` 6.x, region `eu-central-1`. Default model `eu.anthropic.claude-sonnet-5`
(EU cross-region inference profile), configurable by environment variables.

## 6. Conventions

- Google-style docstrings; a module docstring says what the module is for and what it does
  not do yet.
- Tests use the recorded metadata of a real dataset under `tests/fixtures/`; corruptions are
  made on copies in `tmp_path`, never on the fixture.
- Conventional commits (`feat:`, `fix:`, `docs:`, `infra:`, `chore:`), one topic per PR.
- Each milestone closes with: numbers in `README.md`, a `JOURNAL.md` entry, the learning
  guide in `docs/`, and the draft of the milestone's article (kept outside this repository).
