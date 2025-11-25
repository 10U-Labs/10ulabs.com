resource "aws_route53_record" "google_verification" {
  zone_id = module.domain.hosted_zone_id
  name    = module.config.domain_name
  type    = "TXT"
  ttl     = var.gmail_dns_ttl
  records = ["google-site-verification=${var.google_site_verification}"]
}

resource "aws_route53_record" "gmail_mx" {
  zone_id = module.domain.hosted_zone_id
  name    = module.config.domain_name
  type    = "MX"
  ttl     = var.gmail_dns_ttl
  records = ["1 smtp.google.com."]
}
