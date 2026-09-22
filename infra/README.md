# Infrastructure

Everything that runs demosift in AWS is Terraform, in this directory. One state per environment and per
layer. `dev` is the only environment today; the layout is ready for `staging` and `prod`.

## Layout

```
infra/
├── README.md
├── modules/
│   ├── budget/            # monthly AWS Budget + Cost Anomaly Detection (README inside)
│   └── runtime/           # ECR repository, execution role, AgentCore Runtime (README inside)
└── envs/
    └── dev/
        └── foundation/    # root module = one state: providers, backend, variables, module calls, outputs
```

`.tflint.hcl` sits at the repository root and is applied recursively on `infra/`.

| Layer | Modules | Changes |
|---|---|---|
| `foundation` | `budget`, `runtime` | on every agent release (`image_tag`), rarely otherwise |

Later milestones add modules under `modules/`; a resource family that changes at a different cadence than
the runtime gets its own layer (`envs/<env>/<layer>`) and its own state.

## Conventions

- **One state per environment and per layer**, in the account's bucket `demosift-tfstate-<env>-<account id>`,
  key `envs/<env>/<layer>.tfstate`, native lock file (`use_lockfile = true`, no DynamoDB table),
  server-side encryption (S3-managed now; `kms_key_id` once a customer-managed key exists).
- `backend.tf` only declares a partial S3 backend; `backend.hcl` (gitignored) carries bucket, key and
  encryption. `backend.hcl.example` is the template.
- `terraform.tfvars` (gitignored: account ID, e-mail addresses) is copied from `terraform.tfvars.example`.
  The `account_id` validation refuses the placeholder `000000000000`; `allowed_account_ids` on the provider
  refuses any other account.
- **Mandatory tags on every resource**: `project`, `env`, `layer`, `owner`, `data_classification` — set by the
  provider's `default_tags` and passed again as the `tags` variable of modules (validated there).
- A layer reads another layer's outputs through `terraform_remote_state`, added the day an output is consumed
  (never an unused data source).
- Providers: `hashicorp/aws ~> 6.65` (6.65.0 resolved on 2026-09-21). Terraform `>= 1.15.1, < 2.0.0`
  (1.15.8 locally and in CI). 1.15.0 is excluded on purpose: its `validate` checked the required
  arguments of the `backend` block, which fails on a partial backend filled by `-backend-config`; 1.15.1
  removed that check (JOURNAL.md, 2026-09-22). `hashicorp/awscc` is not needed: see the coverage table below.
- Every `.tf` file starts with a one-line comment saying what it does. Everything is in English.
- Provider lock files: the repository `.gitignore` currently ignores `.terraform.lock.hcl`. For roots, a committed
  lock file pins the exact provider build and its checksums; un-ignore `infra/envs/**/.terraform.lock.hcl`
  at the first apply.

## State bucket (created once, by hand)

No bootstrap module in this milestone: the state bucket is created once by hand (below) or later by a tiny
`infra/global/tfstate` root. Versioning, encryption and the public-access block are the three settings that
matter.

```sh
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET="demosift-tfstate-dev-${ACCOUNT_ID}"
aws s3api create-bucket --bucket "$BUCKET" --region eu-central-1 \
  --create-bucket-configuration LocationConstraint=eu-central-1
aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket "$BUCKET" --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"},"BucketKeyEnabled":true}]}'
aws s3api put-public-access-block --bucket "$BUCKET" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

## Dev: init, plan, apply

```sh
cd infra/envs/dev/foundation
cp backend.hcl.example backend.hcl              # replace ACCOUNT_ID
cp terraform.tfvars.example terraform.tfvars    # account_id, notification_emails, image_tag
terraform init -backend-config=backend.hcl
terraform plan
terraform apply
```

**First apply is a two-step**, because the runtime is created from an image that must already exist in the
repository at `image_tag`:

```sh
# 1. repository only
terraform apply -target=module.runtime.aws_ecr_repository.agent -target=module.runtime.aws_ecr_lifecycle_policy.agent
# 2. build (ARM64) and push the image with the tag declared in terraform.tfvars
REPO=$(terraform output -raw ecr_repository_url)
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin "${REPO%%/*}"
docker buildx build --platform linux/arm64 -t "$REPO:0.1.0" --push .
# 3. everything else (budget, role, runtime)
terraform apply
```

Every later release is: push a new tag (tags are immutable), set `image_tag`, `terraform apply` — the runtime
gets a new version behind its `DEFAULT` endpoint.

The runtime creates its own CloudWatch log group; its retention defaults to "never expire". Set it once after
the first apply (see `modules/runtime/README.md`):

```sh
aws logs put-retention-policy --region eu-central-1 --retention-in-days 30 \
  --log-group-name "$(terraform output -raw runtime_log_group_name)"
```

## Local checks

The same commands the CI runs; all four must pass before a change is pushed. tflint in recursive mode
resolves `--config` from each module directory, hence the absolute path. `make tf-check` at the repository
root runs the same four steps.

```sh
terraform fmt -check -recursive infra
terraform -chdir=infra/envs/dev/foundation init -backend=false -input=false
terraform -chdir=infra/envs/dev/foundation validate
tflint --init --config .tflint.hcl
(cd infra && tflint --recursive --config "$(git rev-parse --show-toplevel)/.tflint.hcl")
trivy config --exit-code 1 --severity HIGH,CRITICAL infra
```

Trivy at all severities reports a single LOW finding (AWS-0033, ECR repository not encrypted with a
customer-managed key), accepted and documented in `modules/runtime/README.md`. No inline ignores.

## Region check: `eu-central-1` (Frankfurt), 2026-09-21

Source: the AgentCore "Supported AWS Regions" table
(`docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-regions.html`).

| Capability | Frankfurt | Notes |
|---|---|---|
| AgentCore Runtime (microVMs) | yes | used by this milestone |
| AgentCore Runtime (Instances) | yes | not used |
| AgentCore Gateway | yes | milestone 2 |
| AgentCore Identity | yes | milestone 3 |
| AgentCore Memory | yes | milestone 4; absent from Milan and Spain |
| AgentCore Built-in Tools (Code Interpreter, Browser) | yes | milestone 5 |
| AgentCore Observability | yes | |
| Policy in AgentCore, Evaluations | yes | |
| Bedrock, Claude through EU cross-region profiles (`eu.anthropic.*`) | yes | `eu.anthropic.claude-sonnet-5` listed by the CLI on 2026-09-18 from a sibling project in the same region |

Ireland, London, Paris and Stockholm also carry Runtime, Gateway, Identity and Memory; Frankfurt is kept as
the single region because everything demosift may need is there and the EU inference profiles are invoked
from it. Re-run these two checks at the first apply, from the target account:

```sh
aws bedrock-agentcore-control list-agent-runtimes --region eu-central-1
aws bedrock list-inference-profiles --region eu-central-1 \
  --query "inferenceProfileSummaries[?starts_with(inferenceProfileId, 'eu.anthropic.')].inferenceProfileId"
```

## AgentCore coverage of `hashicorp/aws` 6.65.0 (from `terraform providers schema -json`, 2026-09-21)

`aws_bedrockagentcore_agent_runtime`, `_agent_runtime_endpoint`, `_gateway`, `_gateway_target`, `_gateway_rule`,
`_workload_identity`, `_oauth2_credential_provider`, `_api_key_credential_provider`, `_token_vault_cmk`,
`_memory`, `_memory_strategy`, `_code_interpreter`, `_browser`, `_browser_profile`, `_policy`, `_policy_engine`,
`_evaluator`, `_online_evaluation_config`, `_resource_policy`, `_registry`, `_harness`. Every resource of the
milestones below is covered by the `aws` provider; `awscc` stays unused.

## What exists, what comes next

| Milestone | Content | Where | Status |
|---|---|---|---|
| 1 Foundation | budget with 50/80/100 % actual and 100 % forecast alerts, Cost Anomaly Detection; ECR repository (scan on push, immutable tags, last 10 images); execution role; AgentCore Runtime (`PUBLIC`, `HTTP`, `DEMOSIFT_*` environment) | `modules/budget`, `modules/runtime`, `envs/dev/foundation` | written and validated (fmt, validate, tflint, trivy); not applied yet |
| 2 Gateway | tools exposed to the agent over MCP: `aws_bedrockagentcore_gateway`, `_gateway_target` (Lambda, OpenAPI or MCP targets), `_gateway_rule`; `bedrock-agentcore:InvokeGateway` on the execution role | `modules/gateway` | planned |
| 3 Identity | inbound JWT authorizer on the runtime (`authorizer_configuration`), outbound credential providers for third-party tokens (`_oauth2_credential_provider`, `_api_key_credential_provider`, e.g. the Hugging Face Hub token), explicit `_workload_identity`; deny `GetWorkloadAccessTokenForUserId` | `modules/identity` | planned |
| 4 Memory | `aws_bedrockagentcore_memory` + `_memory_strategy`; unlike the runtime, memory needs an explicit log delivery | `modules/memory` | planned |
| 5 Code Interpreter | custom `aws_bedrockagentcore_code_interpreter` to run dataset checks in a sandbox; execution role permissions for the code interpreter sessions | `modules/tools` | planned |
| Observability | CloudWatch Transaction Search, log retention managed in Terraform, dashboards and alarms | later | planned |
