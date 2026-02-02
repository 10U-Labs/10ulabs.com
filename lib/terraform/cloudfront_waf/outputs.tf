output "web_acl_arn" {
  description = "ARN of the WAF Web ACL"
  value       = var.enabled ? aws_wafv2_web_acl.this[0].arn : ""
}

output "web_acl_id" {
  description = "ID of the WAF Web ACL"
  value       = var.enabled ? aws_wafv2_web_acl.this[0].id : ""
}

output "log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = var.enabled ? aws_cloudwatch_log_group.waf[0].arn : ""
}

output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = var.enabled ? aws_cloudwatch_log_group.waf[0].name : ""
}
