# EventBridge rule for ECS Task State Change (STOPPED)

resource "aws_cloudwatch_event_rule" "task_stopped" {
  name        = local.rule_name
  description = "Capture ECS task stopped events"

  event_pattern = jsonencode({
    source      = ["aws.ecs"]
    detail-type = ["ECS Task State Change"]
    detail = {
      lastStatus = ["STOPPED"]
    }
  })

  tags = merge(local.common_tags, {
    Name = local.rule_name
  })
}

# EventBridge invokes Lambda directly (no SQS queue)
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.task_stopped.name
  target_id = "InvokeLambda"
  arn       = aws_lambda_function.handler.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.task_stopped.arn
}
