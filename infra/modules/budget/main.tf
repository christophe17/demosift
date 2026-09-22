# Monthly AWS Budget with alerts at 50 %, 80 % and 100 % of actual spend and 100 % of forecast, plus an optional
# Cost Anomaly Detection monitor (per AWS service) with a daily e-mail digest.

locals {
  actual_thresholds = [50, 80, 100]
}

resource "aws_budgets_budget" "monthly" {
  name              = var.name
  budget_type       = "COST"
  limit_amount      = tostring(var.limit_usd)
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  time_period_start = var.time_period_start

  dynamic "notification" {
    for_each = local.actual_thresholds
    content {
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      notification_type          = "ACTUAL"
      subscriber_email_addresses = var.notification_emails
    }
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = var.notification_emails
  }
}

# AWS allows a single DIMENSIONAL/SERVICE anomaly monitor per account. If the account already has one (AWS
# creates it automatically on some new accounts), import it here or set enable_anomaly_detection = false.
resource "aws_ce_anomaly_monitor" "services" {
  count = var.enable_anomaly_detection ? 1 : 0

  name              = "${var.name}-anomaly-services"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"
}

# E-mail subscribers only receive DAILY or WEEKLY digests (IMMEDIATE alerts require an SNS topic).
resource "aws_ce_anomaly_subscription" "daily" {
  count = var.enable_anomaly_detection ? 1 : 0

  name             = "${var.name}-anomaly-daily"
  frequency        = "DAILY"
  monitor_arn_list = [aws_ce_anomaly_monitor.services[0].arn]

  dynamic "subscriber" {
    for_each = var.notification_emails
    content {
      type    = "EMAIL"
      address = subscriber.value
    }
  }

  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_ABSOLUTE"
      match_options = ["GREATER_THAN_OR_EQUAL"]
      values        = [tostring(var.anomaly_threshold_usd)]
    }
  }
}
