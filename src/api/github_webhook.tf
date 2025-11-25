resource "random_password" "webhook_secret" {
  length  = 32
  special = true
}

resource "github_repository_webhook" "workflow_job" {
  repository = module.shared.github_repo_name

  configuration {
    url          = "https://${local.domain_subdomain}/v1/runners"
    content_type = "json"
    secret       = random_password.webhook_secret.result
    insecure_ssl = false
  }

  events = ["workflow_job"]
  active = true
}
