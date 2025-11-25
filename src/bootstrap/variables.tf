variable "hosted_zone_id" {
  type = string
}

variable "name_for_cloudtrail" {
  type = string
}

variable "name_for_cloudtrail_log_group" {
  type = string
}

variable "name_for_cloudtrail_iam_role" {
  type = string
}

variable "name_for_github_actions_role" {
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
