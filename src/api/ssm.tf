resource "aws_ssm_parameter" "latest_ami" {
  name        = "/github-runner/ami/latest"
  type        = "String"
  value       = "PLACEHOLDER_UPDATE_AFTER_AMI_BUILD"
  description = "Latest AMI ID for EC2 GitHub self-hosted runners"
  tier        = "Standard"

  lifecycle {
    ignore_changes = [value]
  }

  tags = {
    Name = "github-runner-ami-latest"
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
  name        = var.api_key_parameter_name
  type        = "SecureString"
  value       = random_password.api_key.result
  description = "API key for 10U Labs API authentication"
  tier        = "Standard"

  tags = {
    Name = var.api_key_parameter_name
  }
}
