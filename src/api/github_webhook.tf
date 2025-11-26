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

  events = ["workflow_job"]
  active = true
}
