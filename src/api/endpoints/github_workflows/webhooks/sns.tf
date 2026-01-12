resource "aws_sns_topic" "circuit_open_alerts" {
  name = "${local.resource_prefix}-circuit-open-alerts"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-circuit-open-alerts"
  })
}

resource "aws_sns_topic_subscription" "circuit_opens_email" {
  topic_arn = aws_sns_topic.circuit_open_alerts.arn
  protocol  = "email"
  endpoint  = local.circuit_open_alert_email
}
