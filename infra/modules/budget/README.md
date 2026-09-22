# Module `budget`

Monthly AWS Budget with four e-mail notifications — 50 %, 80 % and 100 % of actual spend, 100 % of the
forecast — plus an optional Cost Anomaly Detection monitor with a daily e-mail digest.

AWS Budgets only accepts US dollars: a cap approved in another currency is entered rounded in USD.

## Resources

| Resource | Purpose |
|---|---|
| `aws_budgets_budget.monthly` | `COST` budget, `MONTHLY`, three `ACTUAL` notifications (50/80/100 %) and one `FORECASTED` (100 %). |
| `aws_ce_anomaly_monitor.services` | `DIMENSIONAL` monitor on the `SERVICE` dimension (one anomaly baseline per AWS service). Created when `enable_anomaly_detection` is true. |
| `aws_ce_anomaly_subscription.daily` | `DAILY` digest to every address of `notification_emails`, filtered on `ANOMALY_TOTAL_IMPACT_ABSOLUTE >= anomaly_threshold_usd`. |

Both services are global: the AWS SDK routes Budgets and Cost Explorer calls to their single endpoint whatever
the provider region.

## Constraints worth knowing

- AWS allows **one `SERVICE` anomaly monitor per account**, and creates one automatically on some new
  accounts. If `apply` fails with a conflict, either import the existing monitor
  (`terraform import 'module.budget.aws_ce_anomaly_monitor.services[0]' <monitor ARN>`) or pass
  `enable_anomaly_detection = false`.
- E-mail subscribers only receive `DAILY` or `WEEKLY` digests; `IMMEDIATE` alerts need an SNS topic.
- Budget notifications are sent by e-mail without confirmation; anomaly digests are also plain e-mail.

## Inputs

| Variable | Default | Description |
|---|---|---|
| `name` | — | Budget name, unique in the account; prefixes the anomaly monitor and subscription names. |
| `limit_usd` | — | Monthly cap in USD (strictly positive). |
| `notification_emails` | — | Recipients of every alert (at least one). |
| `time_period_start` | `2026-09-01_00:00` | Start of the budget period. |
| `enable_anomaly_detection` | `true` | Create the anomaly monitor and its digest. |
| `anomaly_threshold_usd` | `10` | Minimum total impact of an anomaly before it is reported. |

## Outputs

| Output | Description |
|---|---|
| `budget_name` | Name of the budget. |
| `anomaly_monitor_arn` | ARN of the anomaly monitor, `null` when disabled. |
