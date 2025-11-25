module "github_oidc" {
  source = "./modules/github-oidc"

  github_org                   = module.config.github_org
  github_repo                  = module.config.github_repo_name
  aws_account_id               = module.config.aws_account_id
  name_for_github_actions_role = var.name_for_github_actions_role

  depends_on = [module.cloudtrail]
}
