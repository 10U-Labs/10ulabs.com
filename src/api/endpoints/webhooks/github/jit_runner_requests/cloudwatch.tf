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

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-circuit-breaker-open"
  })
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

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-circuit-breaker-high-failures"
  })
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

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-webhook-handler-errors"
  })
}

resource "aws_cloudwatch_metric_alarm" "runners_dlq_messages" {
  alarm_name          = "${local.resource_prefix}-runners-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Average"
  threshold           = 0
  datapoints_to_alarm = 1
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = data.terraform_remote_state.runners.outputs.sqs_dlq_name
  }

  alarm_description = "Runners router DLQ has messages - runner requests are failing"
  alarm_actions     = [aws_sns_topic.circuit_breaker_alerts.arn]

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-runners-dlq-messages"
  })
}
