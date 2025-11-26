resource "aws_ssm_parameter" "github_pat" {
  name  = var.ssm_parameter_name_for_github_pat
  type  = "SecureString"
  value = var.github_pat

  tags = {
    Name = "github-pat"
  }
}
