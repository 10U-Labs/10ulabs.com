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

variable "fargate_runner_labels" {
  type        = list(string)
  description = "Labels for Fargate runners"
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

variable "api_key_parameter_name" {
  type        = string
  description = "API key parameter name"
}

variable "webhook_secret_name" {
  type        = string
  description = "Webhook secret parameter name"
}

variable "github_token_secret_name" {
  type        = string
  description = "GitHub token secret parameter name"
}

variable "ami_promotion_ssm_parameter" {
  type        = string
  description = "SSM parameter name for promoted AMI"
}

variable "ami_promotion_stable_tag" {
  type        = string
  description = "Tag key for stable AMI"
}

variable "github_runner_version" {
  type        = string
  description = "GitHub Actions runner version"
}

variable "packer_spot_retry_attempts" {
  type        = number
  description = "Number of retry attempts for Packer spot instances"
}

variable "packer_spot_retry_delay" {
  type        = number
  description = "Delay in seconds between Packer spot retry attempts"
}
