resource "aws_sns_topic" "circuit_breaker_alerts" {
  name = "${local.resource_prefix}-circuit-breaker-alerts"

  tags = {
    Name = "${local.resource_prefix}-circuit-breaker-alerts"
  }
}

resource "aws_sns_topic_subscription" "circuit_breaker_email" {
  topic_arn = aws_sns_topic.circuit_breaker_alerts.arn
  protocol  = "email"
  endpoint  = var.circuit_breaker_alert_email
}

resource "aws_cloudwatch_metric_alarm" "circuit_breaker_open" {
  alarm_name          = "${local.resource_prefix}-circuit-breaker-open"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 2
  metric_name         = "CircuitBreakerState"
  namespace           = "WebhookRouter"
  period              = 60
  statistic           = "Maximum"
  threshold           = 2.0
  datapoints_to_alarm = 2
  treat_missing_data  = "notBreaching"

  alarm_description = "Circuit breaker has entered OPEN state - webhook processing is failing"
  alarm_actions     = [aws_sns_topic.circuit_breaker_alerts.arn]

  tags = {
    Name = "${local.resource_prefix}-circuit-breaker-open"
  }
}

resource "aws_cloudwatch_metric_alarm" "circuit_breaker_high_failures" {
  alarm_name          = "${local.resource_prefix}-circuit-breaker-high-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "CircuitBreakerState"
  namespace           = "WebhookRouter"
  period              = 60
  statistic           = "Average"
  threshold           = 0.5
  datapoints_to_alarm = 2
  treat_missing_data  = "notBreaching"

  alarm_description = "Circuit breaker failure rate is elevated"
  alarm_actions     = [aws_sns_topic.circuit_breaker_alerts.arn]

  tags = {
    Name = "${local.resource_prefix}-circuit-breaker-high-failures"
  }
}

resource "aws_cloudwatch_metric_alarm" "webhook_handler_errors" {
  alarm_name          = "${local.resource_prefix}-webhook-handler-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = 5

  metric_query {
    id          = "error_rate"
    expression  = "errors / invocations * 100"
    label       = "Error Rate (%)"
    return_data = true
  }

  metric_query {
    id = "errors"
    metric {
      metric_name = "Errors"
      namespace   = "AWS/Lambda"
      period      = 300
      stat        = "Sum"
      dimensions = {
        FunctionName = aws_lambda_function.runners_handler.function_name
      }
    }
  }

  metric_query {
    id = "invocations"
    metric {
      metric_name = "Invocations"
      namespace   = "AWS/Lambda"
      period      = 300
      stat        = "Sum"
      dimensions = {
        FunctionName = aws_lambda_function.runners_handler.function_name
      }
    }
  }

  datapoints_to_alarm = 2
  treat_missing_data  = "notBreaching"
  alarm_description   = "Webhook handler Lambda error rate exceeds 5%"
  alarm_actions       = [aws_sns_topic.circuit_breaker_alerts.arn]

  tags = {
    Name = "${local.resource_prefix}-webhook-handler-errors"
  }
}

resource "aws_cloudwatch_metric_alarm" "job_queue_dlq_messages" {
  alarm_name          = "${local.resource_prefix}-job-queue-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 10
  datapoints_to_alarm = 1
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.job_queue_dlq.name
  }

  alarm_description = "Job queue DLQ has accumulated messages"
  alarm_actions     = [aws_sns_topic.circuit_breaker_alerts.arn]

  tags = {
    Name = "${local.resource_prefix}-job-queue-dlq-messages"
  }
}

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
        value = ["ALARM"]
      }
    }
  })

  tags = {
    Name = "${local.resource_prefix}-circuit-breaker-remediation"
  }
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

  tags = {
    Name = "${local.resource_prefix}-dlq-reprocessor"
  }
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

  tags = {
    Name = "${local.resource_prefix}-circuit-breaker-recovery"
  }
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
