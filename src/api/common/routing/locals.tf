locals {
  api_fqdn              = "api.${module.common.domain_name}"
  aws_account_id        = module.common.aws_account_id
  aws_region            = module.common.aws_region
  domain_name           = module.common.domain_name
  github_repo_full      = "${module.common.github_org}/${module.common.name_for_github_repo}"
  name_for_central_logs = regex("arn:aws:s3:::(.+)$", data.terraform_remote_state.bootstrap.outputs.arn_for_central_logs_bucket)[0]
  resource_prefix       = module.common.resource_prefix

  lambda_role_name = "${local.resource_prefix}CatchAllHandlerServiceRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "API infrastructure"
  }
}
