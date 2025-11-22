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
  name        = "/${var.webhook_secret_name}"
  type        = "String"
  value       = "PLACEHOLDER_WILL_BE_UPDATED"
  description = "GitHub webhook secret for signature verification"
  tier        = "Standard"

  lifecycle {
    ignore_changes = [value]
  }

  tags = {
    Name = var.webhook_secret_name
  }
}

resource "aws_ssm_parameter" "api_key" {
  name        = "/api/key"
  type        = "SecureString"
  value       = random_password.api_key.result
  description = "API key for 10U Labs API authentication"
  tier        = "Standard"

  tags = {
    Name = "api-key"
  }
}
