# EventBridge rule for ECS Task State Change (STOPPED)

resource "aws_cloudwatch_event_rule" "task_stopped" {
  name        = local.rule_name
  description = "Capture ECS task stopped events for runner clusters"

  event_pattern = jsonencode({
    source      = ["aws.ecs"]
    detail-type = ["ECS Task State Change"]
    detail = {
      lastStatus = ["STOPPED"]
      clusterArn = [data.terraform_remote_state.runners_ecs.outputs.cluster_arn]
    }
  })

  tags = merge(local.common_tags, {
    Name = local.rule_name
  })
}

resource "aws_cloudwatch_event_target" "sqs" {
  rule      = aws_cloudwatch_event_rule.task_stopped.name
  target_id = "SendToSQS"
  arn       = aws_sqs_queue.main.arn
}
