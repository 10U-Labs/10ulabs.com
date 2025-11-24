variable "resource_prefix" {
  type        = string
  description = "Prefix for resource names"
}

variable "health_handler_function_name" {
  type        = string
  description = "Health handler Lambda function name"
}

variable "health_handler_log_group_name" {
  type        = string
  description = "Health handler CloudWatch log group name"
}

variable "catchall_handler_function_name" {
  type        = string
  description = "Catchall handler Lambda function name"
}

variable "catchall_handler_log_group_name" {
  type        = string
  description = "Catchall handler CloudWatch log group name"
}

variable "v1_handler_function_name" {
  type        = string
  description = "V1 handler Lambda function name"
}

variable "v1_handler_log_group_name" {
  type        = string
  description = "V1 handler CloudWatch log group name"
}

variable "webhook_handler_log_group_name" {
  type        = string
  description = "Webhook handler CloudWatch log group name"
}

variable "idempotency_table_name" {
  type        = string
  description = "DynamoDB idempotency table name"
}

variable "job_queue_name" {
  type        = string
  description = "SQS job queue name"
}

variable "webhook_dlq_name" {
  type        = string
  description = "SQS webhook DLQ name"
}

variable "job_queue_dlq_name" {
  type        = string
  description = "SQS job queue DLQ name"
}

variable "api_gateway_name" {
  type        = string
  description = "API Gateway name"
}

variable "api_gateway_log_group_name" {
  type        = string
  description = "API Gateway CloudWatch log group name"
}

variable "aws_account_id" {
  type        = string
  description = "AWS account ID"
}

variable "aws_region" {
  type        = string
  description = "AWS region"
}

variable "domain_parent" {
  type        = string
  description = "Parent domain name"
}

variable "domain_subdomain" {
  type        = string
  description = "Subdomain for API"
}

variable "github_repo" {
  type        = string
  description = "GitHub repository (org/repo format)"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for VPC"
}

variable "vpc_max_azs" {
  type        = number
  description = "Maximum number of availability zones"
}

variable "public_subnet_cidr_mask" {
  type        = number
  description = "CIDR mask for public subnets"
}

variable "ecr_repository_name" {
  type        = string
  description = "ECR repository name for GitHub runners"
}

variable "fargate_cpu" {
  type        = string
  description = "Fargate task CPU units"
}

variable "fargate_memory" {
  type        = string
  description = "Fargate task memory in MB"
}

variable "ec2_spot_instance_types" {
  type        = list(string)
  description = "EC2 spot instance types for runners"
}

variable "ec2_max_spot_price" {
  type        = string
  description = "Maximum spot price for EC2 runners"
}

variable "lambda_memory_mb" {
  type        = number
  description = "Lambda function memory in MB"
}

variable "lambda_timeout_seconds" {
  type        = number
  description = "Lambda function timeout in seconds"
}

variable "api_version" {
  type        = string
  description = "API version"
}

variable "stack_name" {
  type        = string
  description = "Stack name for API"
}

variable "vpc_name" {
  type        = string
  description = "VPC name"
}

variable "cluster_name" {
  type        = string
  description = "ECS cluster name"
}

variable "container_name" {
  type        = string
  description = "Container name for GitHub runner"
}

variable "task_family" {
  type        = string
  description = "ECS task family name"
}

variable "log_stream_prefix" {
  type        = string
  description = "CloudWatch log stream prefix"
}

variable "lambda_function_name" {
  type        = string
  description = "Lambda function name"
}

variable "ssm_parameter_name_for_api_key" {
  type        = string
  description = "API key parameter name"
}

variable "ssm_parameter_name_for_webhook_secret" {
  type        = string
  description = "Webhook secret parameter name"
}

variable "circuit_breaker_alert_email" {
  type        = string
  description = "Email address for circuit breaker alert notifications"
}

variable "fargate_cpu_architecture" {
  type        = string
  description = "CPU architecture for Fargate tasks"
}

variable "fargate_operating_system_family" {
  type        = string
  description = "Operating system family for Fargate tasks"
}

variable "ssm_parameter_name_for_ami" {
  type        = string
  description = "SSM parameter name for latest AMI ID"
}
