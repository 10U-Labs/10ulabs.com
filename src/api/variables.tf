variable "catchall_handler_function_name" {
  type = string
}

variable "catchall_handler_log_group_name" {
  type = string
}

variable "v1_handler_function_name" {
  type = string
}

variable "v1_handler_log_group_name" {
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

variable "api_gateway_name" {
  type = string
}

variable "api_gateway_log_group_name" {
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

variable "fargate_cpu" {
  type = string
}

variable "fargate_memory" {
  type = string
}

variable "ec2_spot_instance_types" {
  type = list(string)
}

variable "ec2_max_spot_price" {
  type = string
}

variable "lambda_memory_mb" {
  type = number
}

variable "lambda_timeout_seconds" {
  type = number
}

variable "api_version" {
  type = string
}

variable "stack_name" {
  type = string
}

variable "vpc_name" {
  type = string
}

variable "cluster_name" {
  type = string
}

variable "container_name" {
  type = string
}

variable "task_family" {
  type = string
}

variable "log_stream_prefix" {
  type = string
}

variable "lambda_function_name" {
  type = string
}

variable "ssm_parameter_name_for_api_key" {
  type = string
}

variable "ssm_parameter_name_for_webhook_secret" {
  type = string
}

variable "circuit_breaker_alert_email" {
  type = string
}

variable "fargate_cpu_architecture" {
  type = string
}

variable "fargate_operating_system_family" {
  type = string
}

variable "ssm_parameter_name_for_latest_ami" {
  type = string
}

variable "recaptcha_secret_key" {
  type      = string
  sensitive = true
}
