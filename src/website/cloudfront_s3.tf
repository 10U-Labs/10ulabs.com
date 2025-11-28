resource "aws_s3_bucket" "website" {
  bucket        = local.www_fqdn
  force_destroy = false

  tags = merge(local.common_tags, {
    Name = "${local.www_fqdn}-website"
  })
}

resource "aws_s3_bucket_versioning" "website" {
  bucket = aws_s3_bucket.website.id

  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_public_access_block" "website" {
  bucket = aws_s3_bucket.website.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "website" {
  bucket = aws_s3_bucket.website.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_logging" "website" {
  bucket = aws_s3_bucket.website.id

  target_bucket = local.name_for_central_logs
  target_prefix = "s3-access/website/"
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
      "${aws_s3_bucket.website.arn}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.website.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "website" {
  bucket = aws_s3_bucket.website.id
  policy = data.aws_iam_policy_document.website_bucket_policy.json
}

resource "aws_wafv2_web_acl" "website" {
  provider = aws.us-east-1

  name  = "${local.resource_prefix}WafWebAcl"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.resource_prefix}WafMetrics"
    sampled_requests_enabled   = true
  }

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

resource "aws_cloudfront_function" "spa_routing" {
  name    = "${local.resource_prefix}SpaRoutingFunction"
  runtime = "cloudfront-js-2.0"
  publish = true
  code    = <<-EOT
function handler(event) {
    var request = event.request;
    var host = request.headers.host.value;
    if (host === '${local.apex_fqdn}') {
        return {
            statusCode: 301,
            statusDescription: 'Moved Permanently',
            headers: {
                'location': { value: 'https://${local.www_fqdn}' + request.uri }
            }
        };
    }
    var uri = request.uri;
    if (uri === '/rack-designer' || uri === '/rack-designer/') {
        request.uri = '/rack-designer/index.html';
        return request;
    }
    if (uri.startsWith('/rack-designer/')) {
        return request;
    }
    if (uri.endsWith('/')) {
        request.uri = '/index.html';
    } else if (!uri.includes('.')) {
        request.uri = '/index.html';
    }
    return request;
}
EOT
}

resource "aws_cloudfront_distribution" "website" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  aliases             = [local.www_fqdn, local.apex_fqdn]
  web_acl_id          = aws_wafv2_web_acl.website.arn

  logging_config {
    include_cookies = false
    bucket          = "${local.name_for_central_logs}.s3.amazonaws.com"
    prefix          = "cloudfront-logs/website/"
  }

  origin {
    domain_name              = aws_s3_bucket.website.bucket_regional_domain_name
    origin_id                = "s3-website"
    origin_access_control_id = aws_cloudfront_origin_access_control.website.id
  }

  origin {
    domain_name = replace(replace(aws_lambda_function_url.contact_handler.function_url, "https://", ""), "/", "")
    origin_id   = "contact-api"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  ordered_cache_behavior {
    path_pattern           = "/contact"
    target_origin_id       = "contact-api"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id          = data.aws_cloudfront_cache_policy.caching_disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host_header.id
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

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.spa_routing.arn
    }
  }

  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
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

data "aws_cloudfront_origin_request_policy" "all_viewer_except_host_header" {
  name = "Managed-AllViewerExceptHostHeader"
}

data "aws_cloudfront_cache_policy" "caching_disabled" {
  name = "Managed-CachingDisabled"
}

resource "aws_cloudwatch_log_group" "waf" {
  provider = aws.us-east-1

  name              = "aws-waf-logs-${local.resource_prefix}"
  retention_in_days = 30

  tags = merge(local.common_tags, {
    Name = "aws-waf-logs-${local.resource_prefix}"
  })
}

resource "aws_wafv2_web_acl_logging_configuration" "website" {
  provider = aws.us-east-1

  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]
  resource_arn            = aws_wafv2_web_acl.website.arn
}
