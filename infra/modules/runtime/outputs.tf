# Outputs of the runtime module.

output "ecr_repository_url" {
  description = "URL of the ECR repository (docker push target, without tag)."
  value       = aws_ecr_repository.agent.repository_url
}

output "ecr_repository_arn" {
  description = "ARN of the ECR repository."
  value       = aws_ecr_repository.agent.arn
}

output "runtime_arn" {
  description = "ARN of the AgentCore Runtime (InvokeAgentRuntime target)."
  value       = aws_bedrockagentcore_agent_runtime.agent.agent_runtime_arn
}

output "runtime_id" {
  description = "Identifier of the AgentCore Runtime."
  value       = aws_bedrockagentcore_agent_runtime.agent.agent_runtime_id
}

output "runtime_version" {
  description = "Current version of the AgentCore Runtime (increments on each artifact change)."
  value       = aws_bedrockagentcore_agent_runtime.agent.agent_runtime_version
}

output "role_arn" {
  description = "ARN of the execution role assumed by the runtime."
  value       = aws_iam_role.runtime.arn
}

output "log_group_name" {
  description = "Name of the CloudWatch log group the runtime creates for its DEFAULT endpoint (created by the service, not by Terraform)."
  value       = "/aws/bedrock-agentcore/runtimes/${aws_bedrockagentcore_agent_runtime.agent.agent_runtime_id}-DEFAULT"
}

output "workload_identity_arn" {
  description = "ARN of the workload identity AgentCore assigned to the runtime (consumed by the Identity milestone)."
  value       = one(aws_bedrockagentcore_agent_runtime.agent.workload_identity_details[*].workload_identity_arn)
}
