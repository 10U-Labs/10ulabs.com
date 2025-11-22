resource "aws_ssm_parameter" "github_pat" {
  name  = "/github/pat"
  type  = "SecureString"
  value = var.github_pat

  tags = {
    Name = "github-pat"
  }
}
