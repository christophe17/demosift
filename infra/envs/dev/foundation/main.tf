# Foundation layer of the dev environment: cost guard-rails and the AgentCore Runtime stack (ECR, execution role, runtime).

module "budget" {
  source = "../../../modules/budget"

  name                     = "${local.project}-${local.env}-monthly"
  limit_usd                = var.budget_limit_usd
  notification_emails      = var.notification_emails
  enable_anomaly_detection = var.enable_cost_anomaly_detection
}

module "runtime" {
  source = "../../../modules/runtime"

  project    = local.project
  env        = local.env
  aws_region = var.aws_region
  account_id = var.account_id
  image_tag  = var.image_tag
  model_id   = var.model_id
  tags       = local.tags
}
