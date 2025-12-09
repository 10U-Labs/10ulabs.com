variable "hosted_zone_id" {
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

variable "github_app_private_key" {
  type      = string
  sensitive = true

  validation {
    condition     = length(var.github_app_private_key) > 0
    error_message = "GitHub App private key must not be empty."
  }
}

