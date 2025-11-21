resource "aws_route53_record" "google_verification" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "TXT"
  ttl     = var.ttl
  records = ["google-site-verification=${var.google_site_verification}"]
}

resource "aws_route53_record" "gmail_mx" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "MX"
  ttl     = var.ttl
  records = ["1 smtp.google.com."]
}
