locals {
  api_fqdn         = "api.${module.common.domain_name}"
  aws_account_id   = module.common.aws_account_id
  aws_region       = module.common.aws_region
  github_repo_full = "${module.common.github_org}/${module.common.name_for_github_repo}"
  resource_prefix  = module.common.resource_prefix

  # Lambda configuration
  lambda_function_name  = module.common.lambda_handler_names.runners
  lambda_log_group_name = "/aws/lambda/${module.common.lambda_handler_names.runners}"
  lambda_memory_mb      = 256
  lambda_timeout        = 60

  # SQS queue naming (single queue = endpoint name)
  queue_name     = module.common.lambda_handler_names.runners
  queue_dlq_name = "${module.common.lambda_handler_names.runners}Dlq"

  # IAM role name
  lambda_role_name = "${module.common.lambda_handler_names.runners}Role"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "runners-router"
  }
}
