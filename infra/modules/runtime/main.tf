# ECR repository of the agent image: scan on push, immutable tags, only the N most recent images kept.

locals {
  name_prefix = "${var.project}-${var.env}"

  # AgentCore runtime names only allow letters, digits and underscores (pattern [a-zA-Z][a-zA-Z0-9_]{0,47}).
  agent_runtime_name = replace(local.name_prefix, "-", "_")
}

resource "aws_ecr_repository" "agent" {
  name                 = local.name_prefix
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  # AES256 is the ECR-managed encryption; a customer-managed KMS key would add a fixed monthly cost for an
  # image whose data classification is public.
  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = var.tags
}

resource "aws_ecr_lifecycle_policy" "agent" {
  repository = aws_ecr_repository.agent.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only the ${var.ecr_image_retention_count} most recent images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.ecr_image_retention_count
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
