module "github_oidc" {
  source = "./modules/github-oidc"

  github_org               = module.config.github_org
  github_repo              = module.config.github_repo_name
  aws_account_id           = module.config.aws_account_id
  github_actions_role_name = var.github_actions_role_name

  depends_on = [module.cloudtrail]
}
