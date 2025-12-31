locals {
  api_fqdn         = "api.${module.common.domain_name}"
  aws_account_id   = module.common.aws_account_id
  aws_region       = module.common.aws_region
  etc_dir          = "${path.module}/../../../../../../etc"
  github_org       = module.common.github_org
  github_repo      = module.common.name_for_github_repo
  github_repo_full = "${module.common.github_org}/${module.common.name_for_github_repo}"
  resource_prefix  = module.common.resource_prefix

  # Lambda configuration
  webhook_handler_function_name  = module.common.lambda_handler_names.webhook
  webhook_handler_log_group_name = "/aws/lambda/${module.common.lambda_handler_names.webhook}"
  lambda_memory_mb               = 256
  lambda_timeout_seconds         = 120

  # Resource names derived from webhook handler (PascalCase for SQS queues)
  idempotency_table_name     = "${module.common.lambda_handler_names.webhook}-idempotency"
  webhook_ingress_queue_name = "${module.common.lambda_handler_names.webhook}Ingress"
  webhook_ingress_dlq_name   = "${module.common.lambda_handler_names.webhook}IngressDlq"
  # Note: job_queue removed - routing logic moved to /v1/runners endpoint
  ignored_events_queue_name   = "${module.common.lambda_handler_names.webhook}IgnoredEvents"
  ignored_events_dlq_name     = "${module.common.lambda_handler_names.webhook}IgnoredEventsDlq"
  cancellation_queue_name     = "${module.common.lambda_handler_names.webhook}Cancellations"
  cancellation_queue_dlq_name = "${module.common.lambda_handler_names.webhook}CancellationsDlq"
  webhook_dlq_name            = "${module.common.lambda_handler_names.webhook}Dlq"

  # SSM parameter names
  ssm_parameter_name_for_latest_ami     = module.common.ssm_ec2_runner_ami_latest
  ssm_parameter_name_for_webhook_secret = "/api/webhook-secret"

  # Alerting
  circuit_breaker_alert_email = "jdrowne@10ulabs.com"

  # Lambda function names (single source of truth)
  circuit_breaker_reset_function_name       = "${module.common.resource_prefix}CircuitBreakerReset"
  circuit_breaker_remediation_function_name = "${module.common.resource_prefix}CircuitBreakerRemediation"
  dlq_reprocessor_function_name             = "${module.common.resource_prefix}DLQReprocessor"
  circuit_breaker_recovery_function_name    = "${module.common.resource_prefix}CircuitBreakerRecovery"
  drift_recovery_function_name              = "${module.common.resource_prefix}DriftRecovery"
  spot_interruption_handler_function_name   = "${module.common.resource_prefix}SpotInterruptionHandler"
  stale_runner_cleanup_function_name        = "${module.common.resource_prefix}StaleRunnerCleanup"
  # Note: runner_starter removed - routing logic moved to /v1/runners endpoint
  runner_terminator_function_name       = "${module.common.resource_prefix}RunnerTerminator"
  ignored_events_archiver_function_name = "${module.common.resource_prefix}IgnoredEventsArchiver"

  # IAM role names (single source of truth)
  lambda_runners_handler_role_name      = "${module.common.lambda_handler_names.webhook}ServiceRole"
  circuit_breaker_reset_role_name       = "${module.common.resource_prefix}CircuitBreakerResetRole"
  circuit_breaker_remediation_role_name = "${module.common.resource_prefix}CircuitBreakerRemediationRole"
  dlq_reprocessor_role_name             = "${module.common.resource_prefix}DLQReprocessorRole"
  circuit_breaker_recovery_role_name    = "${module.common.resource_prefix}CircuitBreakerRecoveryRole"
  drift_recovery_role_name              = "${module.common.resource_prefix}DriftRecoveryRole"
  spot_interruption_handler_role_name   = "${module.common.resource_prefix}SpotInterruptionHandlerRole"
  stale_runner_cleanup_role_name        = "${module.common.resource_prefix}StaleRunnerCleanupRole"
  # Note: runner_starter_role removed - routing logic moved to /v1/runners endpoint
  runner_terminator_role_name       = "${module.common.resource_prefix}RunnerTerminatorRole"
  ignored_events_archiver_role_name = "${module.common.resource_prefix}IgnoredEventsArchiverRole"
  config_recorder_role_name         = "${module.common.resource_prefix}ConfigRecorderRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "GitHub self-hosted runners infrastructure"
  }
}
