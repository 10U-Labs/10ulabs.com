# CloudFront WAF Module
#
# Creates a WAFv2 Web ACL for CloudFront with:
# - Default allow action
# - CloudWatch logging
# - Standard visibility config

resource "aws_wafv2_web_acl" "this" {
  provider = aws.us-east-1

  name  = var.name
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = var.metric_name
    sampled_requests_enabled   = true
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "waf" {
  provider = aws.us-east-1

  name              = "aws-waf-logs-${var.log_group_suffix}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_wafv2_web_acl_logging_configuration" "this" {
  provider = aws.us-east-1

  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]
  resource_arn            = aws_wafv2_web_acl.this.arn
}
