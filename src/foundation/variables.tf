variable "aws_region" {
  type = string
}

variable "aws_account_id" {
  type = string
}

variable "github_org" {
  type = string
}

variable "github_repo" {
  type = string
}

variable "domain_name" {
  type = string
}

variable "terraform_state_bucket_name" {
  type = string
}

variable "terraform_state_logs_bucket_name" {
  type = string
}

variable "hosted_zone_id" {
  type = string
}

variable "cloudtrail_name" {
  type = string
}

variable "cloudtrail_bucket_name" {
  type = string
}

variable "cloudtrail_access_logs_bucket_name" {
  type = string
}

variable "cloudtrail_log_group_name" {
  type = string
}

variable "cloudtrail_iam_role_name" {
  type = string
}

variable "github_actions_role_name" {
  type = string
}

variable "google_site_verification" {
  type = string
}

variable "gmail_dns_ttl" {
  type = number
}
