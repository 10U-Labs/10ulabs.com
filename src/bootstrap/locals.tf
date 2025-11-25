locals {
  admin_iam_user                = module.shared.admin_iam_user
  aws_account_id                = module.shared.aws_account_id
  aws_region                    = module.shared.aws_region
  central_logs_bucket_name      = module.shared.central_logs_bucket_name
  domain_name                   = module.shared.domain_name
  github_org                    = module.shared.github_org
  github_repo_name              = module.shared.github_repo_name
  resource_prefix               = module.shared.resource_prefix
  terraform_state_bucket_name   = module.shared.terraform_state_bucket_name

  name_for_cloudtrail           = "${local.resource_prefix}-cloudtrail"
  name_for_cloudtrail_bucket    = module.central_logs.bucket_name
  name_for_cloudtrail_iam_role  = "${local.resource_prefix}-cloudtrail-logs-role"
  name_for_cloudtrail_log_group = "/aws/cloudtrail/${local.resource_prefix}"
  name_for_github_actions_role  = "${local.resource_prefix}-github-actions-role"
}
