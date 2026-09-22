# Input variables of the budget module.

variable "name" {
  description = "Budget name (unique within the account); also prefixes the anomaly monitor and subscription names."
  type        = string
}

variable "limit_usd" {
  description = "Monthly cap in USD (AWS Budgets only handles dollars; an amount approved in another currency is rounded)."
  type        = number

  validation {
    condition     = var.limit_usd > 0
    error_message = "The cap must be strictly positive."
  }
}

variable "notification_emails" {
  description = "Recipients of the alerts at 50 %, 80 % and 100 % of actual spend, 100 % of forecast, and of the anomaly digest."
  type        = list(string)

  validation {
    condition     = length(var.notification_emails) > 0
    error_message = "At least one recipient is required."
  }
}

variable "time_period_start" {
  description = "Start of the budget period, in YYYY-MM-DD_HH:MM format."
  type        = string
  default     = "2026-09-01_00:00"
}

variable "enable_anomaly_detection" {
  description = "Create a Cost Anomaly Detection monitor (per AWS service) and a daily e-mail digest. AWS allows one SERVICE monitor per account: set to false if the account already has one."
  type        = bool
  default     = true
}

variable "anomaly_threshold_usd" {
  description = "Minimum total impact in USD of an anomaly before it appears in the daily digest."
  type        = number
  default     = 10

  validation {
    condition     = var.anomaly_threshold_usd >= 0
    error_message = "The anomaly threshold must be zero or positive."
  }
}
