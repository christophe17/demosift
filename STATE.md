# STATE

**Current milestone: 0 — Foundation.** Started 2026-09-21.

## Done

- Repository bootstrapped: package, tests (20, 90 % coverage), lint and types clean, CLI
  validated on live Hub datasets, Runtime entrypoint with a model-free `inspect` mode,
  Dockerfile for `linux/arm64`, CI workflow.
- Public repository created and pushed 2026-09-22:
  <https://github.com/christophe17/demosift> (personal account for now, D9).
- AWS account chosen 2026-09-25 (D14): the author's existing standalone account. It now
  matters to `demosift-web`, which deploys; nothing here holds its id.
- Infrastructure moved out 2026-09-25 (D15): the Terraform that deployed the Runtime lives in
  `demosift-web`. This repository ships the image and its contract (`docs/01` §5).
- Code Interpreter question closed 2026-09-25 (D16): fixed audits are Lambdas.

## Next steps, in order

Work resumes here. Nothing needs a decision before step 5.

1. **Container contract documented** — done 2026-09-25 (`docs/01` §5), with the execution
   units (`docs/01` §4). Keep the table true: anything the image needs that is not in it is a
   bug in the table.
2. **Wait for the public instance's `runtime` layer** (`~/Sites/demosift-web/STATE.md`,
   step 3). It builds this image from a checkout, pushes it and runs it on AgentCore Runtime.
   Nothing to do here except `make docker-build` when asked.
3. **First invocation through that Runtime**, `inspect` mode then `agent` mode. Record
   latency, tokens and cost per inspection in `JOURNAL.md` and update the table in
   `README.md`; these are the first numbers that do not come from a laptop.
4. **Faithfulness test** of the narrative against the inspection JSON, on real model
   responses (`docs/02-milestones.md`, "How the audit proves itself").
5. **Learning guide** for milestone 0 (`docs/guides/00-foundation.md`), written against what
   was actually deployed, not against what was planned.

Milestone 0 closes when steps 1 to 5 are done and the numbers table carries its first cloud
rows. Milestone 1 is then the numeric audit (`docs/02-milestones.md`).

## Numbers

See the table in `README.md`; all recorded 2026-09-21 on a laptop, none from the cloud yet.

## Pending decisions

- **What the public instance does** is no longer described here: it is specified in
  `~/Sites/demosift-web` (`docs/01` §3 for the three access tiers, `docs/02` for its
  definition of done). This repository only holds the boundary, D12.
- **GitHub organization name** (`docs/03-decisions.md` D9). A repository moves to an
  organization later without losing its history or breaking its links.
