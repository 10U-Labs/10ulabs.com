resource "aws_cloudwatch_log_subscription_filter" "health_handler" {
  name            = "health-handler-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.health_handler.name
  filter_pattern  = ""
  destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn
  role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn
}

resource "aws_cloudwatch_log_subscription_filter" "catchall_handler" {
  name            = "catchall-handler-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.catchall_handler.name
  filter_pattern  = ""
  destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn
  role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn
}

resource "aws_cloudwatch_log_subscription_filter" "runners_handler" {
  name            = "runners-handler-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.runners_handler.name
  filter_pattern  = ""
  destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn
  role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn
}

resource "aws_cloudwatch_log_subscription_filter" "v1_handler" {
  name            = "v1-handler-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.v1_handler.name
  filter_pattern  = ""
  destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn
  role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn
}

resource "aws_cloudwatch_log_subscription_filter" "circuit_breaker_remediation" {
  name            = "circuit-breaker-remediation-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.circuit_breaker_remediation.name
  filter_pattern  = ""
  destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn
  role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn
}

resource "aws_cloudwatch_log_subscription_filter" "dlq_reprocessor" {
  name            = "dlq-reprocessor-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.dlq_reprocessor.name
  filter_pattern  = ""
  destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn
  role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn
}

resource "aws_cloudwatch_log_subscription_filter" "circuit_breaker_recovery" {
  name            = "circuit-breaker-recovery-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.circuit_breaker_recovery.name
  filter_pattern  = ""
  destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn
  role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn
}

resource "aws_cloudwatch_log_subscription_filter" "api_gateway" {
  name            = "api-gateway-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.api_gateway.name
  filter_pattern  = ""
  destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn
  role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn
}

resource "aws_cloudwatch_log_subscription_filter" "ecs_runner" {
  name            = "ecs-runner-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.runner.name
  filter_pattern  = ""
  destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn
  role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn
}
