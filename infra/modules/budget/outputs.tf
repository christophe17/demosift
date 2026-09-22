# Outputs of the budget module.

output "budget_name" {
  description = "Name of the budget created."
  value       = aws_budgets_budget.monthly.name
}

output "anomaly_monitor_arn" {
  description = "ARN of the Cost Anomaly Detection monitor, or null when anomaly detection is disabled."
  value       = one(aws_ce_anomaly_monitor.services[*].arn)
}
