module "website_bucket" {
  source = "../../../lib/terraform/modules/s3_bucket"

  bucket_name         = local.website_bucket_name
  force_destroy       = false
  versioning_enabled  = false
  central_logs_bucket = local.name_for_central_logs
  log_prefix          = "s3-access/website/"

  tags = merge(local.common_tags, {
    Name = "${local.www_fqdn}-website"
  })
}

resource "aws_cloudfront_origin_access_control" "website" {
  name                              = "${local.www_fqdn}-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_iam_policy_document" "website_bucket_policy" {
  statement {
    sid    = "AllowCloudFrontServicePrincipal"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${module.website_bucket.bucket_arn}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.website.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "website" {
  bucket = module.website_bucket.bucket_id
  policy = data.aws_iam_policy_document.website_bucket_policy.json
}

module "website_waf" {
  source = "../../../lib/terraform/modules/cloudfront_waf"

  providers = {
    aws.us-east-1 = aws.us-east-1
  }

  name             = "${local.resource_prefix}WafWebAcl"
  metric_name      = "${local.resource_prefix}WafMetrics"
  log_group_suffix = local.resource_prefix

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}WafWebAcl"
  })
}

resource "aws_cloudfront_response_headers_policy" "website" {
  name = "${local.resource_prefix}ResponseHeadersPolicy"

  security_headers_config {
    strict_transport_security {
      access_control_max_age_sec = 31536000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }
  }
}

resource "aws_cloudfront_cache_policy" "website" {
  name        = "${local.resource_prefix}CachePolicy"
  default_ttl = 86400
  max_ttl     = 31536000
  min_ttl     = 60

  parameters_in_cache_key_and_forwarded_to_origin {
    cookies_config {
      cookie_behavior = "none"
    }

    headers_config {
      header_behavior = "none"
    }

    query_strings_config {
      query_string_behavior = "none"
    }

    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true
  }
}

resource "aws_cloudfront_distribution" "website" {
  enabled         = true
  is_ipv6_enabled = true
  aliases         = [local.www_fqdn, local.apex_fqdn]
  web_acl_id      = module.website_waf.web_acl_arn

  logging_config {
    include_cookies = false
    bucket          = "${local.name_for_central_logs}.s3.amazonaws.com"
    prefix          = "cloudfront-logs/website/"
  }

  origin {
    domain_name              = module.website_bucket.bucket_regional_domain_name
    origin_id                = "s3-website"
    origin_access_control_id = aws_cloudfront_origin_access_control.website.id
  }

  default_cache_behavior {
    target_origin_id       = "s3-website"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id            = aws_cloudfront_cache_policy.website.id
    origin_request_policy_id   = data.aws_cloudfront_origin_request_policy.cors_s3_origin.id
    response_headers_policy_id = aws_cloudfront_response_headers_policy.website.id

    lambda_function_association {
      event_type   = "viewer-request"
      lambda_arn   = aws_lambda_function.spa_routing.qualified_arn
      include_body = false
    }
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/home/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/home/index.html"
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.website.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.www_fqdn}-distribution"
  })

  depends_on = [aws_acm_certificate_validation.website]
}

data "aws_cloudfront_origin_request_policy" "cors_s3_origin" {
  name = "Managed-CORS-S3Origin"
}
