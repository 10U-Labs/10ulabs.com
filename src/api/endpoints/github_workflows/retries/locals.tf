locals {
  aws_region       = module.common.aws_region
  resource_prefix  = module.common.resource_prefix
  github_repo_full = "${module.common.github_org}/${module.common.name_for_github_repo}"

  function_name    = "${local.resource_prefix}GitHubWorkflowsRetries"
  lambda_role_name = "${local.resource_prefix}GitHubWorkflowsRetriesRole"

  common_tags = {
    ManagedBy = "terraform"
    Purpose   = "github-workflows-retries"
  }
}
