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

resource "aws_cloudwatch_event_rule" "ecs_task_stopped" {
  name        = "${local.resource_prefix}-ECSTaskStopped"
  description = "Triggers on ECS task stopped events for spot interruption handling"

  event_pattern = jsonencode({
    source      = ["aws.ecs"]
    detail-type = ["ECS Task State Change"]
    detail = {
      clusterArn = [aws_ecs_cluster.runner.arn]
      lastStatus = ["STOPPED"]
    }
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-ECSTaskStopped"
  })
}

resource "aws_cloudwatch_event_target" "ecs_task_stopped" {
  rule      = aws_cloudwatch_event_rule.ecs_task_stopped.name
  target_id = "SpotInterruptionHandler"
  arn       = aws_lambda_function.spot_interruption_handler.arn
}

resource "aws_lambda_permission" "ecs_task_stopped" {
  statement_id  = "AllowECSTaskStoppedEvent"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.spot_interruption_handler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ecs_task_stopped.arn
}

resource "aws_cloudwatch_event_rule" "ec2_spot_interruption" {
  name        = "${local.resource_prefix}-EC2SpotInterruption"
  description = "Triggers on EC2 spot interruption warnings"

  event_pattern = jsonencode({
    source      = ["aws.ec2"]
    detail-type = ["EC2 Spot Instance Interruption Warning"]
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-EC2SpotInterruption"
  })
}

resource "aws_cloudwatch_event_target" "ec2_spot_interruption" {
  rule      = aws_cloudwatch_event_rule.ec2_spot_interruption.name
  target_id = "SpotInterruptionHandler"
  arn       = aws_lambda_function.spot_interruption_handler.arn
}

resource "aws_lambda_permission" "ec2_spot_interruption" {
  statement_id  = "AllowEC2SpotInterruptionEvent"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.spot_interruption_handler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.ec2_spot_interruption.arn
}

resource "aws_cloudwatch_event_rule" "stale_runner_cleanup_schedule" {
  name                = "${local.resource_prefix}-StaleRunnerCleanupSchedule"
  description         = "Triggers stale runner cleanup every 15 minutes"
  schedule_expression = "rate(15 minutes)"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-StaleRunnerCleanupSchedule"
  })
}

resource "aws_cloudwatch_event_target" "stale_runner_cleanup" {
  rule      = aws_cloudwatch_event_rule.stale_runner_cleanup_schedule.name
  target_id = "StaleRunnerCleanup"
  arn       = aws_lambda_function.stale_runner_cleanup.arn
}

resource "aws_lambda_permission" "stale_runner_cleanup" {
  statement_id  = "AllowScheduledEvent"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.stale_runner_cleanup.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.stale_runner_cleanup_schedule.arn
}
