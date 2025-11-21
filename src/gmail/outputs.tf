output "google_verification_record" {
  value       = aws_route53_record.google_verification.fqdn
  description = "Google site verification TXT record"
}

output "google_verification_value" {
  value       = "google-site-verification=${var.google_site_verification}"
  description = "Google site verification value"
}

output "gmail_mx_record" {
  value       = aws_route53_record.gmail_mx.fqdn
  description = "Gmail MX record"
}
