locals {
  shared_config                 = yamldecode(file("${path.module}/../../../etc/runners.yml"))
  aws_account_id                = module.shared.aws_account_id
  aws_region                    = module.shared.aws_region
  domain_name                   = module.shared.domain_name
  api_fqdn                      = "api.${module.shared.domain_name}"
  ec2_runner_ami_purpose_tag    = "Purpose"
  ec2_runner_ami_purpose_value  = "GitHub self-hosted EC2 runner"
  ec2_runner_ami_stable_tag     = "Stable"
  ec2_runner_managed_by_tag     = "api-ec2-spot-runner"
  github_org                    = module.shared.github_org
  github_repo                   = module.shared.name_for_github_repo
  github_repo_full              = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
  name_for_central_logs         = module.shared.name_for_central_logs_bucket
  resource_prefix               = module.shared.resource_prefix
  runner_label_ec2_spot         = local.shared_config.runner_labels.ec2_spot
  runner_label_ec2_spot_e2e     = local.shared_config.runner_labels.ec2_spot_e2e_test
  runner_label_fargate_spot     = local.shared_config.runner_labels.fargate_spot
  runner_label_fargate_spot_e2e = local.shared_config.runner_labels.fargate_spot_e2e_test

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "API infrastructure"
  }
}
