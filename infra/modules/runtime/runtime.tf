# The AgentCore Runtime itself: container from the ECR repository, managed public egress, HTTP contract on port 8080.

resource "aws_bedrockagentcore_agent_runtime" "agent" {
  agent_runtime_name = local.agent_runtime_name
  description        = var.description
  role_arn           = aws_iam_role.runtime.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${aws_ecr_repository.agent.repository_url}:${var.image_tag}"
    }
  }

  # PUBLIC = service-managed egress to the internet (Bedrock endpoints, Hugging Face Hub); no VPC in this milestone.
  network_configuration {
    network_mode = "PUBLIC"
  }

  # HTTP contract: the ARM64 container listens on 0.0.0.0:8080 and serves POST /invocations and GET /ping.
  protocol_configuration {
    server_protocol = "HTTP"
  }

  environment_variables = {
    DEMOSIFT_MODEL_ID  = var.model_id
    DEMOSIFT_REGION    = var.aws_region
    DEMOSIFT_LOG_LEVEL = var.log_level
  }

  tags = var.tags

  # The service validates the role and pulls the image when the runtime is created: the inline policy must exist first.
  depends_on = [aws_iam_role_policy.runtime]
}
