locals {
  api_fqdn         = "api.${module.shared.domain_name}"
  aws_account_id   = module.shared.aws_account_id
  aws_region       = module.shared.aws_region
  github_org       = module.shared.github_org
  github_repo      = module.shared.name_for_github_repo
  github_repo_full = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
  resource_prefix  = module.shared.resource_prefix

  # Lambda configuration
  webhook_handler_function_name  = module.shared.lambda_handler_names.webhook
  webhook_handler_log_group_name = "/aws/lambda/${module.shared.lambda_handler_names.webhook}"
  lambda_memory_mb               = 256
  lambda_timeout_seconds         = 120

  # Resource names derived from webhook handler
  idempotency_table_name = "${module.shared.lambda_handler_names.webhook}-idempotency"
  job_queue_name         = "${module.shared.lambda_handler_names.webhook}-jobs"
  job_queue_dlq_name     = "${module.shared.lambda_handler_names.webhook}-job-dlq"
  webhook_dlq_name       = "${module.shared.lambda_handler_names.webhook}-dlq"

  # SSM parameter names
  ssm_parameter_name_for_latest_ami     = module.shared.ssm_ec2_runner_ami_latest
  ssm_parameter_name_for_webhook_secret = "/api/webhook-secret"

  # Alerting
  circuit_breaker_alert_email = "jdrowne@10ulabs.com"

  # IAM role names (single source of truth)
  lambda_runners_handler_role_name      = "${module.shared.lambda_handler_names.webhook}ServiceRole"
  circuit_breaker_remediation_role_name = "${module.shared.resource_prefix}CircuitBreakerRemediationRole"
  dlq_reprocessor_role_name             = "${module.shared.resource_prefix}DLQReprocessorRole"
  circuit_breaker_recovery_role_name    = "${module.shared.resource_prefix}CircuitBreakerRecoveryRole"
  drift_recovery_role_name              = "${module.shared.resource_prefix}DriftRecoveryRole"
  spot_interruption_handler_role_name   = "${module.shared.resource_prefix}SpotInterruptionHandlerRole"
  stale_runner_cleanup_role_name        = "${module.shared.resource_prefix}StaleRunnerCleanupRole"
  config_recorder_role_name             = "${module.shared.resource_prefix}ConfigRecorderRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "GitHub self-hosted runners infrastructure"
  }
}
