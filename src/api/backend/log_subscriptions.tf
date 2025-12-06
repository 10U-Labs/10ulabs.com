resource "aws_cloudwatch_log_subscription_filter" "catchall_handler" {
  name            = "catchall-handler-to-firehose"
  log_group_name  = aws_cloudwatch_log_group.catchall_handler.name
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

# WAF log group is in us-east-1 (required for CloudFront WAF), but Firehose is in us-east-2.
# Cross-region log subscriptions require additional infrastructure (Kinesis Data Streams
# with cross-region replication or Lambda). Disabled until cross-region forwarding is set up.
# resource "aws_cloudwatch_log_subscription_filter" "waf" {
#   provider        = aws.us-east-1
#   name            = "waf-to-firehose"
#   log_group_name  = aws_cloudwatch_log_group.waf.name
#   filter_pattern  = ""
#   destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn
#   role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn
# }

resource "aws_cloudwatch_log_subscription_filter" "health_handler" {
  count           = data.terraform_remote_state.health.outputs.log_group_name != "" ? 1 : 0
  name            = "health-handler-to-firehose"
  log_group_name  = data.terraform_remote_state.health.outputs.log_group_name
  filter_pattern  = ""
  destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn
  role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn
}
