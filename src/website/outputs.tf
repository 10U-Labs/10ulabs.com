output "bucket_name" {
  value = aws_s3_bucket.website.id
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.website.id
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.website.domain_name
}

output "website_domain_name" {
  value = local.www_fqdn
}

output "website_url" {
  value = "https://${local.www_fqdn}"
}

output "contact_form_api_url" {
  value = aws_lambda_function_url.contact_handler.function_url
}
