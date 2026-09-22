# Input variables of the dev foundation root (values in terraform.tfvars, see terraform.tfvars.example).

variable "aws_region" {
  description = "Single AWS region of the project (EU)."
  type        = string
  default     = "eu-central-1"

  validation {
    condition     = contains(["eu-central-1", "eu-west-1", "eu-west-3", "eu-north-1", "eu-south-1", "eu-south-2"], var.aws_region)
    error_message = "The region must be a European Union region."
  }
}

variable "account_id" {
  description = "AWS account ID of this environment; the provider refuses any other account."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id)) && var.account_id != "000000000000"
    error_message = "Account ID not filled in: copy terraform.tfvars.example to terraform.tfvars and set the real account ID."
  }
}

variable "owner" {
  description = "Value of the owner tag (person responsible for the resources)."
  type        = string
  default     = "christophe"
}

variable "notification_emails" {
  description = "Recipients of the budget alerts and of the cost anomaly digest."
  type        = list(string)

  validation {
    condition     = length(var.notification_emails) > 0
    error_message = "At least one recipient is required."
  }
}

variable "budget_limit_usd" {
  description = "Monthly cap of the account in USD."
  type        = number
  default     = 50
}

variable "enable_cost_anomaly_detection" {
  description = "Create the Cost Anomaly Detection monitor and its daily digest (set to false if the account already has a per-service monitor)."
  type        = bool
  default     = true
}

variable "image_tag" {
  description = "Tag of the agent image to run (pushed to the ECR repository before apply; tags are immutable)."
  type        = string
}

variable "model_id" {
  description = "EU cross-region inference profile the agent calls (DEMOSIFT_MODEL_ID)."
  type        = string
  default     = "eu.anthropic.claude-sonnet-5"
}
