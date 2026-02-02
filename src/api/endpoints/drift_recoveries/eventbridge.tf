# EventBridge rule to trigger drift recovery checks on a schedule
resource "aws_cloudwatch_event_rule" "scheduled_check" {
  name                = "${local.resource_prefix}-scheduled-check"
  description         = "Triggers periodic drift recovery checks"
  schedule_expression = "rate(1 hour)"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-scheduled-check"
  })
}

# EventBridge invokes Lambda directly
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.scheduled_check.name
  target_id = "InvokeLambda"
  arn       = aws_lambda_function.handler.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled_check.arn
}
