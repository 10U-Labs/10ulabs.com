resource "aws_ssm_parameter" "latest_ami" {
  name  = local.ssm_parameter_name_for_latest_ami
  type  = "String"
  value = "PLACEHOLDER_UPDATE_AFTER_AMI_BUILD"
  tier  = "Standard"

  lifecycle {
    ignore_changes = [value]
  }

  tags = merge(local.common_tags, {
    Name = local.ssm_parameter_name_for_latest_ami
  })
}

resource "aws_ssm_parameter" "webhook_secret" {
  name        = local.ssm_parameter_name_for_webhook_secret
  type        = "String"
  value       = random_password.webhook_secret.result
  description = "GitHub webhook secret for signature verification"
  tier        = "Standard"

  tags = merge(local.common_tags, {
    Name = local.ssm_parameter_name_for_webhook_secret
  })
}

resource "random_password" "webhook_secret" {
  length  = 32
  special = true
}

resource "github_repository_webhook" "workflow_job" {
  repository = local.github_repo

  configuration {
    url          = "https://${local.api_fqdn}/v1/runners"
    content_type = "json"
    secret       = random_password.webhook_secret.result
    insecure_ssl = false
  }

  events = ["workflow_job", "workflow_run"]
  active = true
}
