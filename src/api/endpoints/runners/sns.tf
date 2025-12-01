resource "aws_sns_topic" "circuit_breaker_alerts" {
  name = "${local.resource_prefix}-circuit-breaker-alerts"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-circuit-breaker-alerts"
  })
}

resource "aws_sns_topic_subscription" "circuit_breaker_email" {
  topic_arn = aws_sns_topic.circuit_breaker_alerts.arn
  protocol  = "email"
  endpoint  = var.circuit_breaker_alert_email
}
