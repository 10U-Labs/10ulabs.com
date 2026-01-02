resource "aws_ses_email_identity" "contact" {
  email = "contact@${local.domain_name}"
}

resource "aws_ssm_parameter" "recaptcha_secret" {
  name        = "/10ulabs/contact/recaptcha-secret-key"
  description = "Google reCAPTCHA v3 secret key for contact form verification"
  type        = "SecureString"
  value       = var.recaptcha_secret_key

  tags = merge(local.common_tags, {
    Name = "10ulabs-contact-recaptcha-secret"
  })
}
