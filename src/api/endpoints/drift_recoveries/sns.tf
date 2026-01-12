resource "aws_sns_topic" "alerts" {
  name = "${local.resource_prefix}-drift-recovery-alerts"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-drift-recovery-alerts"
  })
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = local.alert_email
}
