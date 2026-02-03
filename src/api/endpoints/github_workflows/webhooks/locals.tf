locals {
  api_fqdn         = "api.${module.common.domain_name}"
  aws_account_id   = module.common.aws_account_id
  aws_region       = module.common.aws_region
  etc_dir          = "${path.module}/../../../../../etc"
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
  ignored_events_queue_name  = "${module.common.lambda_handler_names.webhook}IgnoredEvents"
  ignored_events_dlq_name    = "${module.common.lambda_handler_names.webhook}IgnoredEventsDlq"
  webhook_dlq_name           = "${module.common.lambda_handler_names.webhook}Dlq"

  # SSM parameter names
  ssm_parameter_name_for_webhook_secret = "/api/webhook-secret"

  # Alerting
  circuit_open_alert_email = "jdrowne@10ulabs.com"

  # Lambda function names (single source of truth)
  circuit_opens_function_name             = module.common.lambda_handler_names.circuit_opens
  circuit_open_remediations_function_name = module.common.lambda_handler_names.circuit_open_remediations
  circuit_open_recoveries_function_name   = module.common.lambda_handler_names.circuit_open_recoveries
  dlq_reprocessor_function_name           = "${module.common.resource_prefix}DLQReprocessor"
  ignored_events_archiver_function_name   = "${module.common.resource_prefix}IgnoredEventsArchiver"

  # IAM role names (single source of truth)
  lambda_runners_handler_role_name    = "${module.common.lambda_handler_names.webhook}ServiceRole"
  circuit_opens_role_name             = "${module.common.lambda_handler_names.circuit_opens}Role"
  circuit_open_remediations_role_name = "${module.common.lambda_handler_names.circuit_open_remediations}Role"
  circuit_open_recoveries_role_name   = "${module.common.lambda_handler_names.circuit_open_recoveries}Role"
  dlq_reprocessor_role_name           = "${module.common.resource_prefix}DLQReprocessorRole"
  ignored_events_archiver_role_name   = "${module.common.resource_prefix}IgnoredEventsArchiverRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "GitHub self-hosted runners infrastructure"
  }
}
