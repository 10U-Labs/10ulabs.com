# Subscription filters to route CloudWatch Logs to Firehose for archival in S3
#
# These filters connect each Lambda log group to the centralized Firehose
# delivery stream, which writes logs to the central-logs S3 bucket.

locals {
  firehose_arn      = data.terraform_remote_state.api.outputs.firehose_cloudwatch_logs_arn
  firehose_role_arn = data.terraform_remote_state.api.outputs.cloudwatch_logs_firehose_role_arn
  # Only create subscription filters if Firehose exists (api_common_routing deployed)
  create_subscriptions = local.firehose_arn != ""
}

resource "aws_cloudwatch_log_subscription_filter" "runners_handler" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "runners-handler-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.runners_handler.name
  filter_pattern  = ""
  destination_arn = local.firehose_arn
  role_arn        = local.firehose_role_arn
}

resource "aws_cloudwatch_log_subscription_filter" "circuit_open_recoveries" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "circuit-open-recovery-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.circuit_open_recoveries.name
  filter_pattern  = ""
  destination_arn = local.firehose_arn
  role_arn        = local.firehose_role_arn
}

resource "aws_cloudwatch_log_subscription_filter" "circuit_open_remediations" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "circuit-open-remediation-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.circuit_open_remediations.name
  filter_pattern  = ""
  destination_arn = local.firehose_arn
  role_arn        = local.firehose_role_arn
}

resource "aws_cloudwatch_log_subscription_filter" "circuit_opens" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "circuit-open-reset-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.circuit_opens.name
  filter_pattern  = ""
  destination_arn = local.firehose_arn
  role_arn        = local.firehose_role_arn
}

resource "aws_cloudwatch_log_subscription_filter" "dlq_reprocessor" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "dlq-reprocessor-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.dlq_reprocessor.name
  filter_pattern  = ""
  destination_arn = local.firehose_arn
  role_arn        = local.firehose_role_arn
}

resource "aws_cloudwatch_log_subscription_filter" "ignored_events_archiver" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "ignored-events-archiver-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.ignored_events_archiver.name
  filter_pattern  = ""
  destination_arn = local.firehose_arn
  role_arn        = local.firehose_role_arn
}
