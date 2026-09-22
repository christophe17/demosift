# Terraform and provider version constraints of the budget module.
terraform {
  required_version = ">= 1.15.1, < 2.0.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.65"
    }
  }
}
