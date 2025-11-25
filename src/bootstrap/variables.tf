variable "hosted_zone_id" {
  type = string
}

variable "cloudtrail_name" {
  type = string
}

variable "cloudtrail_bucket_name" {
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

variable "github_pat" {
  type      = string
  sensitive = true

  validation {
    condition     = length(var.github_pat) > 0
    error_message = "GitHub PAT must not be empty."
  }
}
