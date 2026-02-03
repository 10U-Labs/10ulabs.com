resource "aws_cloudwatch_event_rule" "circuit_open_remediations" {
  name        = "${local.resource_prefix}-circuit-open-remediation"
  description = "Triggers circuit open remediation when alarm state changes"

  event_pattern = jsonencode({
    source      = ["aws.cloudwatch"]
    detail-type = ["CloudWatch Alarm State Change"]
    detail = {
      alarmName = [
        aws_cloudwatch_metric_alarm.circuit_open_open.alarm_name,
        aws_cloudwatch_metric_alarm.webhook_handler_errors.alarm_name
      ]
      state = {
        value = ["ALARM", "OK"]
      }
    }
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-circuit-open-remediation"
  })
}

resource "aws_cloudwatch_event_target" "circuit_open_remediations" {
  rule      = aws_cloudwatch_event_rule.circuit_open_remediations.name
  target_id = "CircuitOpenRemediationsLambda"
  arn       = aws_lambda_function.circuit_open_remediations.arn
}

resource "aws_lambda_permission" "circuit_open_remediations_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.circuit_open_remediations.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.circuit_open_remediations.arn
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

resource "aws_cloudwatch_event_rule" "circuit_open_recoveries" {
  name                = "${local.resource_prefix}-circuit-open-recovery"
  description         = "Attempts automatic recovery of circuit open every 5 minutes"
  schedule_expression = "rate(5 minutes)"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-circuit-open-recovery"
  })
}

resource "aws_cloudwatch_event_target" "circuit_open_recoveries" {
  rule      = aws_cloudwatch_event_rule.circuit_open_recoveries.name
  target_id = "CircuitOpenRecoveriesLambda"
  arn       = aws_lambda_function.circuit_open_recoveries.arn
}

resource "aws_lambda_permission" "circuit_open_recoveries_eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.circuit_open_recoveries.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.circuit_open_recoveries.arn
}
