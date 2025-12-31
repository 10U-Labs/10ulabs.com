locals {
  aws_account_id       = module.common.aws_account_id
  aws_region           = module.common.aws_region
  ecr_repository_arn   = data.terraform_remote_state.api_common_docker_repository.outputs.ecr_repository_arn
  ecr_repository_name  = data.terraform_remote_state.api_common_docker_repository.outputs.ecr_repository_name
  github_repo_full     = "${module.common.github_org}/${module.common.name_for_github_repo}"
  lambda_function_name = "${local.resource_prefix}ImageForEcsRunnersHandler"
  lambda_role_name     = "${local.resource_prefix}ImageForEcsRunnersHandlerServiceRole"
  resource_prefix      = module.common.resource_prefix

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "image-for-ecs-runners"
  }
}
