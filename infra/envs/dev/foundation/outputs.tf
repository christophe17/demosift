# Outputs of the dev foundation root, read by later layers through terraform_remote_state and by the CI.

output "ecr_repository_url" {
  description = "URL of the ECR repository receiving the agent image."
  value       = module.runtime.ecr_repository_url
}

output "runtime_arn" {
  description = "ARN of the AgentCore Runtime (InvokeAgentRuntime target)."
  value       = module.runtime.runtime_arn
}

output "runtime_id" {
  description = "Identifier of the AgentCore Runtime."
  value       = module.runtime.runtime_id
}

output "runtime_role_arn" {
  description = "ARN of the runtime execution role."
  value       = module.runtime.role_arn
}

output "runtime_log_group_name" {
  description = "CloudWatch log group the runtime creates for its DEFAULT endpoint."
  value       = module.runtime.log_group_name
}

output "budget_name" {
  description = "Name of the monthly budget."
  value       = module.budget.budget_name
}

output "runtime_workload_identity_arn" {
  description = "ARN of the workload identity assigned to the runtime."
  value       = module.runtime.workload_identity_arn
}
