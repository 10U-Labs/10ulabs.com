variable "name" {
  description = "Name of the WAF Web ACL"
  type        = string
}

variable "metric_name" {
  description = "CloudWatch metric name for WAF"
  type        = string
}

variable "log_group_suffix" {
  description = "Suffix for the CloudWatch log group name (prefixed with 'aws-waf-logs-')"
  type        = string
}

variable "log_retention_days" {
  description = "Number of days to retain WAF logs"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
