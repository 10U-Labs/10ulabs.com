locals {
  aws_account_id               = module.shared.aws_account_id
  aws_region                   = module.shared.aws_region
  domain_name                  = module.shared.domain_name
  api_fqdn             = "api.${module.shared.domain_name}"
  ec2_runner_ami_purpose_tag   = "Purpose"
  ec2_runner_ami_purpose_value = "GitHub self-hosted EC2 runner"
  ec2_runner_ami_stable_tag    = "Stable"
  github_org                   = module.shared.github_org
  github_repo                  = module.shared.name_for_github_repo
  github_repo_full             = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
  name_for_central_logs        = module.shared.name_for_central_logs_bucket
  resource_prefix              = module.shared.resource_prefix
}
