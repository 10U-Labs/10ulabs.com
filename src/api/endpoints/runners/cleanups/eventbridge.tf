# EventBridge Scheduler for periodic cleanup (every 5 minutes)

resource "aws_scheduler_schedule" "cleanup" {
  name       = local.schedule_name
  group_name = "default"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(5 minutes)"

  target {
    arn      = aws_lambda_function.handler.arn
    role_arn = aws_iam_role.scheduler.arn

    input = jsonencode({
      source = "scheduled"
    })
  }

  state = "ENABLED"
}
