variable "contact_handler_function_name" {
  type = string
}

variable "contact_handler_log_group_name" {
  type = string
}

variable "recaptcha_secret_key" {
  type      = string
  sensitive = true
}
