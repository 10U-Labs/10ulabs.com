resource "aws_ssm_parameter" "api_key" {
  name  = var.ssm_parameter_name_for_api_key
  type  = "SecureString"
  value = random_password.api_key.result
  tier  = "Standard"

  tags = merge(local.common_tags, {
    Name = var.ssm_parameter_name_for_api_key
  })
}
