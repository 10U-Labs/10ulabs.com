resource "aws_ssm_parameter" "latest_ami" {
  name        = var.ssm_parameter_name_for_ami
  type        = "String"
  value       = "PLACEHOLDER_UPDATE_AFTER_AMI_BUILD"
  tier        = "Standard"

  lifecycle {
    ignore_changes = [value]
  }

  tags = {
    Name = var.ssm_parameter_name_for_ami
  }
}

resource "aws_ssm_parameter" "webhook_secret" {
  name        = var.webhook_secret_name
  type        = "String"
  value       = random_password.webhook_secret.result
  description = "GitHub webhook secret for signature verification"
  tier        = "Standard"

  tags = {
    Name = var.webhook_secret_name
  }
}

resource "aws_ssm_parameter" "api_key" {
  name        = var.ssm_parameter_name_for_api_key
  type        = "SecureString"
  value       = random_password.api_key.result
  tier        = "Standard"

  tags = {
    Name = var.ssm_parameter_name_for_api_key
  }
}
