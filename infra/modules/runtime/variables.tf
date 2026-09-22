# Input variables of the runtime module.

variable "project" {
  description = "Short project name, prefix of every resource."
  type        = string

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,15}$", var.project))
    error_message = "The project name is lowercase letters, digits and hyphens, 2 to 16 characters."
  }
}

variable "env" {
  description = "Target environment: dev, staging or prod."
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env must be dev, staging or prod."
  }
}

variable "aws_region" {
  description = "Region hosting the runtime, the ECR repository and the log groups; also the region of the EU cross-region inference profiles the role may invoke."
  type        = string
}

variable "account_id" {
  description = "AWS account ID, used to scope the trust policy and the resource ARNs of the execution role."
  type        = string

  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "The account ID is 12 digits."
  }
}

variable "image_tag" {
  description = "Tag of the container image in the ECR repository (tags are immutable: one tag per build). The image must be pushed before the runtime is created or updated."
  type        = string

  validation {
    condition     = can(regex("^[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}$", var.image_tag))
    error_message = "The image tag follows the Docker tag syntax (up to 128 characters, no leading '.' or '-')."
  }
}

variable "model_id" {
  description = "Bedrock inference profile ID passed to the agent as DEMOSIFT_MODEL_ID. Must be an EU cross-region profile (eu.*), the only ones the execution role may invoke."
  type        = string

  validation {
    condition     = startswith(var.model_id, "eu.")
    error_message = "model_id must be an EU cross-region inference profile ID (prefix eu.)."
  }
}

variable "log_level" {
  description = "Log level passed to the agent as DEMOSIFT_LOG_LEVEL."
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR"], var.log_level)
    error_message = "log_level must be DEBUG, INFO, WARNING or ERROR."
  }
}

variable "description" {
  description = "Description of the agent runtime, shown in the AgentCore console."
  type        = string
  default     = "demosift: multi-agent auditor of LeRobot robot-demonstration datasets"
}

variable "ecr_image_retention_count" {
  description = "Number of most recent images kept by the ECR lifecycle policy; older ones expire."
  type        = number
  default     = 10

  validation {
    condition     = var.ecr_image_retention_count >= 1 && floor(var.ecr_image_retention_count) == var.ecr_image_retention_count
    error_message = "ecr_image_retention_count is a positive integer."
  }
}

variable "tags" {
  description = "Tags common to all resources; the keys project, env, layer, owner and data_classification are mandatory."
  type        = map(string)

  validation {
    condition = alltrue([
      for key in ["project", "env", "layer", "owner", "data_classification"] : contains(keys(var.tags), key)
    ])
    error_message = "The tags project, env, layer, owner and data_classification are mandatory."
  }
}
