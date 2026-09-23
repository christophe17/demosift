# STATE

**Current milestone: 0 — Foundation.** Started 2026-09-21.

## Done

- Repository bootstrapped: package, tests (20, 90 % coverage), lint and types clean, CLI
  validated on live Hub datasets, Runtime entrypoint with a model-free `inspect` mode,
  Dockerfile for `linux/arm64`, CI workflow, Terraform foundation layer (budget, ECR, Runtime)
  validated offline.
- Public repository created and pushed 2026-09-22:
  <https://github.com/christophe17/demosift> (personal account for now, D9).

## Next steps, in order

Work resumes here. Steps 1 and 5 need a decision from the author; everything else follows
from them and can be done in one sitting each.

1. **Pick the AWS account** *(decision needed)*: reuse an existing one or open a new one.
   Then create the Terraform state bucket and fill `backend.hcl` and `terraform.tfvars`
   (`infra/README.md`).
2. **Apply the foundation in two steps**: ECR first, push the `linux/arm64` runtime image,
   then the full apply, because the Runtime needs an image to pull.
3. **First invocation through AgentCore Runtime**, `inspect` mode then `agent` mode. Record
   latency, tokens and cost per inspection in `JOURNAL.md` and update the table in
   `README.md`; these are the first numbers that do not come from a laptop.
4. **Faithfulness test** of the narrative against the inspection JSON, on real model
   responses (`docs/02-milestones.md`, "How the audit proves itself").
5. **Start building `demosift-web`** (D12, D13). The repository exists and is fully specified
   at `~/Sites/demosift-web`; its own `STATE.md` orders its steps. It calls the Runtime
   deployed at step 2; nothing of it lands in this repository.
6. **Per-user quota and budget alarm** on a real address, then play the "costs tripled
   overnight" runbook once (`docs/05-cost-and-security.md` §5).
7. **Learning guide** for milestone 0 (`docs/guides/00-foundation.md`), written against what
   was actually deployed, not against what was planned.

Milestone 0 closes when steps 1 to 7 are done and the numbers table carries its first cloud
rows. Milestone 1 is then the numeric audit (`docs/02-milestones.md`).

## Numbers

See the table in `README.md`; all recorded 2026-09-21 on a laptop, none from the cloud yet.

## Pending decisions

- **AWS account** (step 1): reused or new.
- **What the public instance does** is no longer described here: it is specified in
  `~/Sites/demosift-web` (`docs/01` §3 for the three access tiers, `docs/02` for its
  definition of done). This repository only holds the boundary, D12.
- **GitHub organization name** (`docs/03-decisions.md` D9). A repository moves to an
  organization later without losing its history or breaking its links.
