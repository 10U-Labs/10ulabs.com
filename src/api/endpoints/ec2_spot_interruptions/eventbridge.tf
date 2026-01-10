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

resource "aws_cloudwatch_event_target" "sqs" {
  rule      = aws_cloudwatch_event_rule.spot_interruption.name
  target_id = "SendToSQS"
  arn       = aws_sqs_queue.main.arn
}
