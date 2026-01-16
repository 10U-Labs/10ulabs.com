# EventBridge rule for EC2 Spot Instance Interruption Warning

resource "aws_cloudwatch_event_rule" "spot_interruption" {
  name        = local.rule_name
  description = "Capture EC2 Spot Instance Interruption Warnings"

  event_pattern = jsonencode({
    source      = ["aws.ec2"]
    detail-type = ["EC2 Spot Instance Interruption Warning"]
  })

  tags = merge(local.common_tags, {
    Name = local.rule_name
  })
}

# EventBridge invokes Lambda directly (no SQS queue)
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.spot_interruption.name
  target_id = "InvokeLambda"
  arn       = aws_lambda_function.handler.arn
}

resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.handler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.spot_interruption.arn
}
