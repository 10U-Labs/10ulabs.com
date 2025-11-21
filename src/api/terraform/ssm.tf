resource "aws_ssm_parameter" "github_token" {
  name        = "/github-runner/credentials"
  type        = "String"
  value       = "PLACEHOLDER_UPDATE_WITH_GITHUB_TOKEN"
  description = "GitHub Personal Access Token for self-hosted runners"
  tier        = "Standard"

  lifecycle {
    ignore_changes = [value]
  }

  tags = {
    Name = "github-runner-credentials"
  }
}

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
