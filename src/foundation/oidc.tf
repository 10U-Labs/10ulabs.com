module "github_oidc" {
  source = "./modules/github-oidc"

  github_org               = var.github_org
  github_repo              = var.github_repo
  aws_account_id           = var.aws_account_id
  github_actions_role_name = var.github_actions_role_name

  depends_on = [module.cloudtrail]
}
