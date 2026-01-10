resource "aws_cloudwatch_event_rule" "circuit_breaker_remediation" {
  name        = "${local.resource_prefix}-circuit-breaker-remediation"
  description = "Triggers circuit breaker remediation when alarm state changes"

  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]
    detail-type = ["CloudWatch Alarm State Change"]
    detail = {
      alarmName = [
        aws_cloudwatch_metric_alarm.circuit_breaker_open.alarm_name,
        aws_cloudwatch_metric_alarm.webhook_handler_errors.alarm_name
      ]
      state = {
        value = ["ALARM", "OK"]
      }
    }
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-circuit-breaker-remediation"
  })
}

resource "aws_cloudwatch_event_target" "circuit_breaker_remediation" {
  rule      = aws_cloudwatch_event_rule.circuit_breaker_remediation.name
  target_id = "CircuitBreakerRemediationLambda"
  arn       = aws_lambda_function.circuit_breaker_remediation.arn
}

resource "aws_lambda_permission" "circuit_breaker_remediation_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.circuit_breaker_remediation.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.circuit_breaker_remediation.arn
}

resource "aws_cloudwatch_event_rule" "dlq_reprocessor" {
  name                = "${local.resource_prefix}-dlq-reprocessor"
  description         = "Triggers DLQ reprocessor every 15 minutes"
  schedule_expression = "rate(15 minutes)"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-dlq-reprocessor"
  })
}

resource "aws_cloudwatch_event_target" "dlq_reprocessor" {
  rule      = aws_cloudwatch_event_rule.dlq_reprocessor.name
  target_id = "DLQReprocessorLambda"
  arn       = aws_lambda_function.dlq_reprocessor.arn
}

resource "aws_lambda_permission" "dlq_reprocessor_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dlq_reprocessor.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.dlq_reprocessor.arn
}

resource "aws_cloudwatch_event_rule" "circuit_breaker_recovery" {
  name                = "${local.resource_prefix}-circuit-breaker-recovery"
  description         = "Attempts automatic recovery of circuit breaker every 5 minutes"
  schedule_expression = "rate(5 minutes)"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-circuit-breaker-recovery"
  })
}

resource "aws_cloudwatch_event_target" "circuit_breaker_recovery" {
  rule      = aws_cloudwatch_event_rule.circuit_breaker_recovery.name
  target_id = "CircuitBreakerRecoveryLambda"
  arn       = aws_lambda_function.circuit_breaker_recovery.arn
}

resource "aws_lambda_permission" "circuit_breaker_recovery_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.circuit_breaker_recovery.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.circuit_breaker_recovery.arn
}

# Note: ECS task stopped and EC2 spot interruption EventBridge rules removed
# - Migrated to /v1/ec2-spot-interruptions endpoint
# - Migrated to /v1/ecs-task-stops endpoint

# Note: Stale runner cleanup schedule removed
# - Migrated to /v1/runners/cleanups endpoint
