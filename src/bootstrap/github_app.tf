resource "aws_ssm_parameter" "github_app_id" {
  name  = "${module.common.github_app.ssm_prefix}/id"
  type  = "String"
  value = module.common.github_app.id

  tags = {
    Name = "github-app-id"
  }
}

resource "aws_ssm_parameter" "github_app_installation_id" {
  name  = "${module.common.github_app.ssm_prefix}/installation_id"
  type  = "String"
  value = module.common.github_app.installation_id

  tags = {
    Name = "github-app-installation-id"
  }
}

resource "aws_ssm_parameter" "github_app_private_key" {
  name  = "${module.common.github_app.ssm_prefix}/private_key"
  type  = "SecureString"
  value = var.github_app_private_key

  tags = {
    Name = "github-app-private-key"
  }
}
