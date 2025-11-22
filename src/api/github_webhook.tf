resource "random_password" "webhook_secret" {
  length  = 32
  special = true
}

resource "github_repository_webhook" "workflow_job" {
  repository = "10ulabs.com"

  configuration {
    url          = "https://${var.domain_subdomain}/v1/runners"
    content_type = "json"
    secret       = random_password.webhook_secret.result
    insecure_ssl = false
  }

  events = ["workflow_job"]
  active = true
}

resource "null_resource" "update_webhook_secret_ssm" {
  triggers = {
    webhook_secret = random_password.webhook_secret.result
  }

  provisioner "local-exec" {
    command = <<-EOT
      aws ssm put-parameter \
        --name "${aws_ssm_parameter.webhook_secret.name}" \
        --value "${random_password.webhook_secret.result}" \
        --type String \
        --overwrite \
        --region ${var.aws_region}
    EOT
  }

  depends_on = [
    github_repository_webhook.workflow_job,
    aws_ssm_parameter.webhook_secret
  ]
}
