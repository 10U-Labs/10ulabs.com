locals {
  api_fqdn         = "api.${module.shared.domain_name}"
  aws_account_id   = module.shared.aws_account_id
  aws_region       = module.shared.aws_region
  github_repo_full = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
  resource_prefix  = module.shared.resource_prefix

  # Lambda configuration
  lambda_function_name  = module.shared.lambda_handler_names.runners
  lambda_log_group_name = "/aws/lambda/${module.shared.lambda_handler_names.runners}"
  lambda_memory_mb      = 256
  lambda_timeout        = 60

  # SQS queue naming (single queue = endpoint name)
  queue_name     = module.shared.lambda_handler_names.runners
  queue_dlq_name = "${module.shared.lambda_handler_names.runners}Dlq"

  # IAM role name
  lambda_role_name = "${module.shared.lambda_handler_names.runners}Role"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "runners-router"
  }
}
