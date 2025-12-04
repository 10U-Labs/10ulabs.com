locals {
  shared_config             = yamldecode(file("${path.module}/../../../../etc/runners.yml"))
  api_fqdn                  = "api.${module.shared.domain_name}"
  aws_account_id            = module.shared.aws_account_id
  aws_region                = module.shared.aws_region
  github_org                = module.shared.github_org
  github_repo               = module.shared.name_for_github_repo
  github_repo_full          = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
  resource_prefix           = module.shared.resource_prefix
  runner_label_ec2     = local.shared_config.runner_labels.ec2
  runner_label_ec2_e2e = local.shared_config.runner_labels.ec2_e2e_test
  runner_label_fargate      = local.shared_config.runner_labels.fargate
  runner_label_fargate_e2e  = local.shared_config.runner_labels.fargate_e2e_test

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "GitHub self-hosted runners infrastructure"
  }
}
