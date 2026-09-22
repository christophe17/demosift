# Module `runtime`

The Amazon Bedrock AgentCore Runtime stack of one environment: the ECR repository holding the agent image,
the execution role the runtime assumes, and the runtime itself.

## Resources

| Resource | Name | Purpose |
|---|---|---|
| `aws_ecr_repository.agent` | `<project>-<env>` | Image repository: scan on push, **immutable tags** (one tag per build), AES256 encryption. |
| `aws_ecr_lifecycle_policy.agent` | — | Expires every image beyond the `ecr_image_retention_count` most recent ones (default 10). |
| `aws_iam_role.runtime` | `<project>-<env>-agentcore-runtime` | Execution role. Trust: `bedrock-agentcore.amazonaws.com` with `aws:SourceAccount = <account>` and `ArnLike aws:SourceArn = arn:aws:bedrock-agentcore:<region>:<account>:*`, as documented by AWS. |
| `aws_iam_role_policy.runtime` | — | Least-privilege inline policy (table below). |
| `aws_bedrockagentcore_agent_runtime.agent` | `<project>_<env>` | The runtime: container `<repository>:<image_tag>`, network mode `PUBLIC`, server protocol `HTTP`, environment variables `DEMOSIFT_MODEL_ID`, `DEMOSIFT_REGION`, `DEMOSIFT_LOG_LEVEL`. |

Runtime names only allow `[a-zA-Z][a-zA-Z0-9_]{0,47}`, hence `demosift_dev` with an underscore while every
other resource is `demosift-dev`.

### Execution role permissions

| Sid | Actions | Resource | Why |
|---|---|---|---|
| `EcrImageAccess` | `ecr:BatchGetImage`, `ecr:GetDownloadUrlForLayer` | this repository | pull the agent image |
| `EcrTokenAccess` | `ecr:GetAuthorizationToken` | `*` | no resource-level support for this action |
| `LogsGroups` | `logs:CreateLogGroup`, `logs:DescribeLogStreams` | `log-group:/aws/bedrock-agentcore/runtimes/*` | the runtime creates its own log group |
| `LogsResourcePolicy` | `logs:PutResourcePolicy` | `log-group:/aws/bedrock-agentcore/runtimes/<runtime name>-*` | lets X-Ray deliver spans into the runtime's log group |
| `LogsDescribeGroups` | `logs:DescribeLogGroups` | `log-group:*` | as documented by AWS |
| `LogsStreams` | `logs:CreateLogStream`, `logs:PutLogEvents` | `.../runtimes/*:log-stream:*` | write logs |
| `XRayTelemetry` | `xray:PutTraceSegments`, `xray:PutTelemetryRecords`, `xray:GetSamplingRules`, `xray:GetSamplingTargets` | `*` | OpenTelemetry traces (ADOT); no resource-level support |
| `CloudWatchMetrics` | `cloudwatch:PutMetricData` | `*`, condition `cloudwatch:namespace = bedrock-agentcore` | custom metrics; no resource-level support |
| `BedrockModelInvocation` | `bedrock:InvokeModel`, `bedrock:InvokeModelWithResponseStream` | `inference-profile/eu.*` in this region, `arn:aws:bedrock:eu-*::foundation-model/*` | EU cross-region inference profiles and the EU foundation models they route to |
| `GetAgentAccessToken` | `bedrock-agentcore:GetWorkloadAccessToken`, `...ForJWT`, `...ForUserId` | `workload-identity-directory/default` and `.../workload-identity/<runtime name>-*` | the runtime's own workload identity |

AWS recommends denying `GetWorkloadAccessTokenForUserId` once JWT tokens are available; this is left for the
Identity milestone.

## Decisions

- **No explicit CloudWatch log group.** The AWS observability guide states that "when you create an AgentCore
  runtime resource (agent), by default, AgentCore runtime creates a CloudWatch log group for the
  service-provided logs", named `/aws/bedrock-agentcore/runtimes/<runtime id>-<endpoint name>`; the documented
  execution role carries `logs:CreateLogGroup` for exactly that. Pre-creating the group in Terraform would race
  the service. Consequence: retention is "never expire" by default. Set it once after the first deployment:

  ```sh
  aws logs put-retention-policy --region eu-central-1 --retention-in-days 30 \
    --log-group-name "$(terraform output -raw runtime_log_group_name)"
  ```

  The Observability milestone may import the group into Terraform to manage retention declaratively.
- **AES256 on ECR** rather than a customer-managed KMS key: the image's data classification is public and a
  key would add a fixed monthly cost. Trivy reports this as LOW only.
- **`depends_on` from the runtime to the inline policy**: the service validates the role and pulls the image
  when the runtime is created; without it the first apply can fail on a role that exists but has no policy yet.

## Container contract (HTTP protocol)

The image must be built for **ARM64** (`docker buildx build --platform linux/arm64`), listen on
`0.0.0.0:8080`, and serve `POST /invocations` (JSON in, JSON or SSE out) and `GET /ping`
(`{"status": "Healthy"}`). The image must exist in the repository at `image_tag` **before** the runtime is
created or updated; see the root README for the first-apply ordering.

## Inputs

| Variable | Default | Description |
|---|---|---|
| `project` | — | Short project name, resource prefix. |
| `env` | — | `dev`, `staging` or `prod`. |
| `aws_region` | — | Region of the runtime, repository and log groups. |
| `account_id` | — | Account ID scoping the trust policy and ARNs. |
| `image_tag` | — | Image tag to run (immutable; pushed beforehand). |
| `model_id` | — | EU cross-region inference profile (`eu.*`), passed as `DEMOSIFT_MODEL_ID`. |
| `log_level` | `INFO` | Passed as `DEMOSIFT_LOG_LEVEL`. |
| `description` | demosift description | Runtime description. |
| `ecr_image_retention_count` | `10` | Images kept by the lifecycle policy. |
| `tags` | — | Mandatory tag keys: `project`, `env`, `layer`, `owner`, `data_classification`. |

## Outputs

| Output | Description |
|---|---|
| `ecr_repository_url` | Push target (`docker tag … <url>:<tag>`). |
| `ecr_repository_arn` | Repository ARN. |
| `runtime_arn` | Runtime ARN, the `InvokeAgentRuntime` target. |
| `runtime_id` | Runtime identifier. |
| `runtime_version` | Runtime version, incremented on each artifact change. |
| `role_arn` | Execution role ARN. |
| `log_group_name` | Log group the service creates for the `DEFAULT` endpoint. |
