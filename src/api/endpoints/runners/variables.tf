variable "webhook_handler_function_name" {
  type = string
}

variable "webhook_handler_log_group_name" {
  type = string
}

variable "idempotency_table_name" {
  type = string
}

variable "job_queue_name" {
  type = string
}

variable "webhook_dlq_name" {
  type = string
}

variable "job_queue_dlq_name" {
  type = string
}

variable "vpc_cidr" {
  type = string
}

variable "vpc_max_azs" {
  type = number
}

variable "public_subnet_cidr_mask" {
  type = number
}

variable "lambda_memory_mb" {
  type = number
}

variable "lambda_timeout_seconds" {
  type = number
}

variable "vpc_name" {
  type = string
}

variable "ssm_parameter_name_for_webhook_secret" {
  type = string
}

variable "circuit_breaker_alert_email" {
  type = string
}

variable "ssm_parameter_name_for_latest_ami" {
  type = string
}
