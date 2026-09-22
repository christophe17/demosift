# STATE

**Current milestone: 0 — Foundation.** Started 2026-09-21.

## Done

- Repository bootstrapped: package, tests (20, 90 % coverage), lint and types clean, CLI
  validated on live Hub datasets, Runtime entrypoint with a model-free `inspect` mode,
  Dockerfile for `linux/arm64`, CI workflow, Terraform foundation layer (budget, ECR, Runtime)
  validated offline.

## Pending in milestone 0

- [ ] Choose the AWS account and create the Terraform state bucket (see `infra/README.md`).
- [ ] `terraform apply` of `envs/dev/foundation`; push the runtime image; first invocation
      through AgentCore Runtime; record latency and tokens in `JOURNAL.md`.
- [ ] Authentication and per-user quota in front of the Runtime; budget alarm wired to a
      real email address.
- [ ] Faithfulness test of the agent's narrative against the inspection JSON (needs the
      first Bedrock call; see `docs/02-milestones.md`, "How the audit proves itself").
- [ ] Learning guide for milestone 0 (`docs/guides/00-foundation.md`).
- [x] Choose the GitHub organization; create the public repository; first push.
      Personal account for now (D9): <https://github.com/christophe17/demosift>,
      first push 2026-09-22.

## Numbers

See the table in `README.md`; all recorded 2026-09-21 on a laptop, none from the cloud yet.

## Pending decisions

- GitHub organization name (`docs/03-decisions.md` D9).
- Whether the public instance signs users in with Hugging Face OAuth from milestone 0 or
  only from milestone 1 (write-back into dataset cards needs it in any case).
