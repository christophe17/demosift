# Execution role assumed by AgentCore Runtime: trust limited to this account's runtimes, least-privilege inline policy
# (docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html, "AgentCore Runtime execution role").

data "aws_iam_policy_document" "runtime_trust" {
  statement {
    sid     = "AssumeRolePolicy"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["bedrock-agentcore.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:bedrock-agentcore:${var.aws_region}:${var.account_id}:*"]
    }
  }
}

resource "aws_iam_role" "runtime" {
  name               = "${local.name_prefix}-agentcore-runtime"
  description        = "Execution role of the ${local.name_prefix} AgentCore Runtime"
  assume_role_policy = data.aws_iam_policy_document.runtime_trust.json

  tags = var.tags
}

data "aws_iam_policy_document" "runtime_permissions" {
  # Pull the agent image from this repository only.
  statement {
    sid       = "EcrImageAccess"
    effect    = "Allow"
    actions   = ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"]
    resources = [aws_ecr_repository.agent.arn]
  }

  # ecr:GetAuthorizationToken does not support resource-level permissions.
  statement {
    sid       = "EcrTokenAccess"
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  # Service-provided logs land in /aws/bedrock-agentcore/runtimes/<runtime-id>-<endpoint>; the runtime creates the
  # group itself with these permissions.
  statement {
    sid       = "LogsGroups"
    effect    = "Allow"
    actions   = ["logs:CreateLogGroup", "logs:DescribeLogStreams"]
    resources = ["arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"]
  }

  # Lets AgentCore authorise X-Ray to deliver spans into the runtime's own log group (unified span destination).
  statement {
    sid       = "LogsResourcePolicy"
    effect    = "Allow"
    actions   = ["logs:PutResourcePolicy"]
    resources = ["arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:/aws/bedrock-agentcore/runtimes/${local.agent_runtime_name}-*"]
  }

  statement {
    sid       = "LogsDescribeGroups"
    effect    = "Allow"
    actions   = ["logs:DescribeLogGroups"]
    resources = ["arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:*"]
  }

  statement {
    sid       = "LogsStreams"
    effect    = "Allow"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:${var.aws_region}:${var.account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"]
  }

  # OpenTelemetry traces (ADOT) are shipped through X-Ray, which has no resource-level permissions.
  statement {
    sid       = "XRayTelemetry"
    effect    = "Allow"
    actions   = ["xray:PutTraceSegments", "xray:PutTelemetryRecords", "xray:GetSamplingRules", "xray:GetSamplingTargets"]
    resources = ["*"]
  }

  # Custom metrics, restricted to the AgentCore namespace (PutMetricData has no resource-level permissions).
  statement {
    sid       = "CloudWatchMetrics"
    effect    = "Allow"
    actions   = ["cloudwatch:PutMetricData"]
    resources = ["*"]

    condition {
      test     = "StringEquals"
      variable = "cloudwatch:namespace"
      values   = ["bedrock-agentcore"]
    }
  }

  # Model invocation through EU cross-region inference profiles, which fan out to foundation models in EU regions.
  statement {
    sid     = "BedrockModelInvocation"
    effect  = "Allow"
    actions = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
    resources = [
      "arn:aws:bedrock:${var.aws_region}:${var.account_id}:inference-profile/eu.*",
      "arn:aws:bedrock:eu-*::foundation-model/*",
    ]
  }

  # Workload identity of this runtime (AgentCore Identity). AWS recommends denying GetWorkloadAccessTokenForUserId
  # once JWT tokens are available; to revisit in the Identity milestone.
  statement {
    sid    = "GetAgentAccessToken"
    effect = "Allow"
    actions = [
      "bedrock-agentcore:GetWorkloadAccessToken",
      "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
      "bedrock-agentcore:GetWorkloadAccessTokenForUserId",
    ]
    resources = [
      "arn:aws:bedrock-agentcore:${var.aws_region}:${var.account_id}:workload-identity-directory/default",
      "arn:aws:bedrock-agentcore:${var.aws_region}:${var.account_id}:workload-identity-directory/default/workload-identity/${local.agent_runtime_name}-*",
    ]
  }
}

resource "aws_iam_role_policy" "runtime" {
  name   = "${local.name_prefix}-agentcore-runtime"
  role   = aws_iam_role.runtime.id
  policy = data.aws_iam_policy_document.runtime_permissions.json
}
