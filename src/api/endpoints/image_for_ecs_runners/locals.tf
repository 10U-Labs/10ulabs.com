locals {
  aws_account_id      = module.shared.aws_account_id
  aws_region          = module.shared.aws_region
  ecr_repository_arn  = data.terraform_remote_state.bootstrap.outputs.ecr_runners_repository_arn
  ecr_repository_name = data.terraform_remote_state.bootstrap.outputs.ecr_runners_repository_name
  github_repo_full    = "${module.shared.github_org}/${module.shared.name_for_github_repo}"
  resource_prefix     = module.shared.resource_prefix

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "image-for-ecs-runners"
  }
}
