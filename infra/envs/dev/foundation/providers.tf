# AWS provider of the dev foundation root: single EU region, account pinned, mandatory tags applied by default.

locals {
  project = "demosift"
  env     = "dev"
  layer   = "foundation"

  tags = {
    project             = local.project
    env                 = local.env
    layer               = local.layer
    owner               = var.owner
    data_classification = "public"
  }
}

provider "aws" {
  region              = var.aws_region
  allowed_account_ids = [var.account_id]

  default_tags {
    tags = local.tags
  }
}
