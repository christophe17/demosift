# CLAUDE.md — demosift

Read first. This file gives the context, the non-negotiable rules and the reading order.

## 1. The project in one sentence

A deterministic auditor of LeRobot robot-demonstration datasets: a library and a command line
that read a dataset from the Hugging Face Hub, check it, and write a quality report, with no
model, no agent and no cloud account involved.

## 2. Context

- **Public repository, real users.** The users are the LeRobot community; the tool must be
  useful to them for free, and honest about what it can and cannot see.
- **A library first.** A hosted instance imports this package and builds an assistant, a
  pipeline and a front end around it, in a separate repository. Anything that only exists
  because there is a hosted instance with users (a model call, an agent, sign-in, quotas,
  infrastructure) does not belong here.
- **Everything is in English**: code, comments, docs, commit messages, issues.
- **The author learns by reading.** Claude Code writes the code and, for each milestone, the
  guide that explains it (`docs/`). A milestone without its guide and its numbers is not done.
- **Bought conventions.** Quality rules and CI shape are inherited from the author's earlier
  project (`cgp-ai`); the domain is new.

## 3. Reading order

1. `docs/01-architecture.md` — what the library is and is not, its modules, its public surface, how a deployment uses it
2. `docs/02-milestones.md` — milestones, how the audit proves itself, what is excluded
3. `docs/03-decisions.md` — decision log
4. `docs/04-lerobot-dataset-format.md` — the v3.0 format as observed, and what each check verifies
5. `docs/05-bounds-and-robustness.md` — input bounds, hostile inputs, what is measured

**Session resume:** read `CLAUDE.md`, `STATE.md` (current milestone, numbers, pending
decisions) and `JOURNAL.md` (dated history) before answering.

## 4. Non-negotiable rules

1. **No model, no network beyond the Hub.** The library calls no language or vision model and
   reaches nothing but `huggingface.co`. Where a milestone needs a model's verdict (the visual
   audit), the library defines the interface and the calibration, and the caller supplies the
   model.
2. **No number in a document without a run.** A figure in `README.md` or `docs/` cites the
   `JOURNAL.md` entry that produced it. "Not measured yet" is an acceptable value; a guess is
   not.
3. **No secrets in the repository.** The only credential the library ever touches is the Hub
   token, read by `huggingface_hub` from the environment; the CI scans for secrets.
4. **Scope guard.** Work only on the current milestone (`STATE.md`). An idea outside it becomes
   an issue, not a change.
5. **Format honesty.** Only LeRobot codebase v3.0 is read; other versions are refused with an
   explicit error, never guessed at.
6. **This repository deploys nothing.** It publishes a package and a command-line image; running
   them anywhere is somebody else's repository. No Terraform, no cloud resource, no account id.
7. **Production quality from the first commit**: typed (`mypy --strict`), linted (`ruff`),
   tested (`pytest`, real recorded fixtures), no `TODO`, explicit errors, bounded downloads.
8. **A public surface is a contract.** What `demosift/__init__.py` exports is versioned;
   removing or renaming any of it is a major version, and the changelog says so.
9. **No conclusion from a single run.** Any metric about a model-backed component (the visual
   audit's verdicts, once a caller supplies a model) is published from N runs with an interval;
   overlapping intervals are reported as "not significant".
10. **A verdict is published only once calibrated.** A visual-audit criterion becomes a verdict
    when its agreement with the gold set is measured (`docs/02`, "How the audit proves
    itself"); before that it is labelled indicative.
11. **Hostile input is expected.** Anyone can publish a dataset. Every reader has a size bound
    and an explicit error; a malformed file never becomes a crash or a silent wrong number
    (`docs/05`).

## 5. Stack

Python 3.12, `uv`, `src/` layout, single package `demosift`. `pydantic` models, `pandas` +
`pyarrow` for parquet, `huggingface_hub` for the Hub, `click` for the CLI. Nothing else at
runtime. Released as a wheel on a `v*` tag (GitHub release, PyPI once trusted publishing is set
up) and as a command-line image on GHCR.

## 6. Conventions

- Google-style docstrings; a module docstring says what the module is for and what it does
  not do yet.
- Tests use the recorded metadata of a real dataset under `tests/fixtures/`; corruptions are
  made on copies in `tmp_path`, never on the fixture.
- Conventional commits (`feat:`, `fix:`, `docs:`, `chore:`), one topic per PR.
- Each milestone closes with: numbers in `README.md`, a `JOURNAL.md` entry, the learning
  guide in `docs/`, and a release tag.
