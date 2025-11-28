resource "aws_ses_email_identity" "contact" {
  email = "contact@${local.domain_name}"
}

resource "aws_ssm_parameter" "recaptcha_secret" {
  name        = "/${local.resource_prefix}/recaptcha-secret-key"
  description = "Google reCAPTCHA v3 secret key for contact form verification"
  type        = "SecureString"
  value       = var.recaptcha_secret_key

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-recaptcha-secret"
  })
}
