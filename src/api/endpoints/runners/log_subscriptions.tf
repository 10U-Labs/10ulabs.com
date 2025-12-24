# Subscription filters to route CloudWatch Logs to Firehose for archival in S3
#
# These filters connect each Lambda log group to the centralized Firehose
# delivery stream, which writes logs to the central-logs S3 bucket.

locals {
  firehose_arn      = data.terraform_remote_state.api.outputs.firehose_cloudwatch_logs_arn
  firehose_role_arn = data.terraform_remote_state.api.outputs.cloudwatch_logs_firehose_role_arn
  # Only create subscription filters if Firehose exists (api_backend deployed)
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

resource "aws_cloudwatch_log_subscription_filter" "runner_starter" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "runner-starter-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.runner_starter.name
  filter_pattern  = ""
  destination_arn = local.firehose_arn
  role_arn        = local.firehose_role_arn
}

resource "aws_cloudwatch_log_subscription_filter" "runner_terminator" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "runner-terminator-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.runner_terminator.name
  filter_pattern  = ""
  destination_arn = local.firehose_arn
  role_arn        = local.firehose_role_arn
}

resource "aws_cloudwatch_log_subscription_filter" "circuit_breaker_recovery" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "circuit-breaker-recovery-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.circuit_breaker_recovery.name
  filter_pattern  = ""
  destination_arn = local.firehose_arn
  role_arn        = local.firehose_role_arn
}

resource "aws_cloudwatch_log_subscription_filter" "circuit_breaker_remediation" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "circuit-breaker-remediation-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.circuit_breaker_remediation.name
  filter_pattern  = ""
  destination_arn = local.firehose_arn
  role_arn        = local.firehose_role_arn
}

resource "aws_cloudwatch_log_subscription_filter" "circuit_breaker_reset" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "circuit-breaker-reset-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.circuit_breaker_reset.name
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

resource "aws_cloudwatch_log_subscription_filter" "drift_recovery" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "drift-recovery-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.drift_recovery.name
  filter_pattern  = ""
  destination_arn = local.firehose_arn
  role_arn        = local.firehose_role_arn
}

resource "aws_cloudwatch_log_subscription_filter" "health_check" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "health-check-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.health_check.name
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

resource "aws_cloudwatch_log_subscription_filter" "spot_interruption_handler" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "spot-interruption-handler-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.spot_interruption_handler.name
  filter_pattern  = ""
  destination_arn = local.firehose_arn
  role_arn        = local.firehose_role_arn
}

resource "aws_cloudwatch_log_subscription_filter" "stale_runner_cleanup" {
  count           = local.create_subscriptions ? 1 : 0
  name            = "stale-runner-cleanup-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.stale_runner_cleanup.name
  filter_pattern  = ""
  destination_arn = local.firehose_arn
  role_arn        = local.firehose_role_arn
}
