resource "aws_ssm_parameter" "github_pat" {
  name  = module.common.ssm_github_pat_name
  type  = "SecureString"
  value = var.github_pat

  tags = {
    Name = "github-pat"
  }
}
