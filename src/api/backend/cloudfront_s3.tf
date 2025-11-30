resource "aws_s3_bucket" "docs" {
  bucket        = local.api_fqdn
  force_destroy = true

  tags = merge(local.common_tags, {
    Name = "${local.api_fqdn}-docs"
  })
}

resource "aws_s3_bucket_versioning" "docs" {
  bucket = aws_s3_bucket.docs.id

  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_public_access_block" "docs" {
  bucket = aws_s3_bucket.docs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "docs" {
  bucket = aws_s3_bucket.docs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_logging" "docs" {
  bucket = aws_s3_bucket.docs.id

  target_bucket = local.name_for_central_logs
  target_prefix = "s3-access/api-docs/"
}

resource "aws_s3_object" "index_html" {
  bucket       = aws_s3_bucket.docs.id
  key          = "index.html"
  source       = "${path.module}/../../www/api/index.html"
  content_type = "text/html"
  etag         = filemd5("${path.module}/../../www/api/index.html")
}

resource "aws_s3_object" "not_found_html" {
  bucket       = aws_s3_bucket.docs.id
  key          = "404.html"
  source       = "${path.module}/../../www/api/404.html"
  content_type = "text/html"
  etag         = filemd5("${path.module}/../../www/api/404.html")
}

resource "aws_s3_object" "openapi_yml" {
  bucket       = aws_s3_bucket.docs.id
  key          = "openapi.yml"
  source       = "${path.module}/../../www/api/openapi.yml"
  content_type = "application/x-yaml"
  etag         = filemd5("${path.module}/../../www/api/openapi.yml")
}

resource "aws_cloudfront_origin_access_control" "s3" {
  name                              = "${local.api_fqdn}-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

data "aws_iam_policy_document" "s3_bucket_policy" {
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
      "${aws_s3_bucket.docs.arn}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [aws_cloudfront_distribution.main.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "docs" {
  bucket = aws_s3_bucket.docs.id
  policy = data.aws_iam_policy_document.s3_bucket_policy.json
}

resource "aws_wafv2_web_acl" "api" {
  provider = aws.us-east-1

  name  = "ApiWafWebAcl"
  scope = "CLOUDFRONT"

  default_action {
    allow {}
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "ApiWafMetrics"
    sampled_requests_enabled   = true
  }

  tags = merge(local.common_tags, {
    Name = "ApiWafWebAcl"
  })
}

resource "aws_cloudfront_cache_policy" "docs" {
  name        = "ApiDocsCachePolicy"
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

resource "aws_cloudfront_function" "url_rewrite" {
  name    = "RootUrlRewriteFunction"
  runtime = "cloudfront-js-2.0"
  publish = true
  code    = <<-EOT
function handler(event) {
    var request = event.request;
    if (request.uri === '/') {
        request.uri = '/index.html';
    }
    return request;
}
EOT
}

resource "aws_cloudfront_distribution" "main" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = ""
  aliases             = [local.api_fqdn]
  web_acl_id          = aws_wafv2_web_acl.api.arn

  logging_config {
    include_cookies = false
    bucket          = "${local.name_for_central_logs}.s3.amazonaws.com"
    prefix          = "cloudfront-logs/api/"
  }

  origin {
    domain_name         = "${aws_api_gateway_rest_api.main.id}.execute-api.${local.aws_region}.amazonaws.com"
    origin_id           = "api-gateway"
    origin_path         = "/prod"
    connection_attempts = 3
    connection_timeout  = 10

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  origin {
    domain_name              = aws_s3_bucket.docs.bucket_regional_domain_name
    origin_id                = "s3-docs"
    origin_access_control_id = aws_cloudfront_origin_access_control.s3.id
  }

  default_cache_behavior {
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id          = data.aws_cloudfront_cache_policy.disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host_header.id
  }

  ordered_cache_behavior {
    path_pattern           = "/"
    target_origin_id       = "s3-docs"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id          = aws_cloudfront_cache_policy.docs.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.cors_s3_origin.id

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.url_rewrite.arn
    }
  }

  ordered_cache_behavior {
    path_pattern           = "/openapi.yml"
    target_origin_id       = "s3-docs"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id          = aws_cloudfront_cache_policy.docs.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.cors_s3_origin.id
  }

  ordered_cache_behavior {
    path_pattern           = "/404.html"
    target_origin_id       = "s3-docs"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id          = aws_cloudfront_cache_policy.docs.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.cors_s3_origin.id
  }

  ordered_cache_behavior {
    path_pattern           = "/health"
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id          = data.aws_cloudfront_cache_policy.disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host_header.id
  }

  ordered_cache_behavior {
    path_pattern           = "/v1/*"
    target_origin_id       = "api-gateway"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true

    cache_policy_id          = data.aws_cloudfront_cache_policy.disabled.id
    origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host_header.id
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.api.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.api_fqdn}-distribution"
  })

  depends_on = [aws_acm_certificate_validation.api]
}

data "aws_cloudfront_cache_policy" "disabled" {
  name = "Managed-CachingDisabled"
}

data "aws_cloudfront_origin_request_policy" "all_viewer_except_host_header" {
  name = "Managed-AllViewerExceptHostHeader"
}

data "aws_cloudfront_origin_request_policy" "cors_s3_origin" {
  name = "Managed-CORS-S3Origin"
}

resource "aws_cloudwatch_log_group" "waf" {
  provider = aws.us-east-1

  name              = "aws-waf-logs-api"
  retention_in_days = 30

  tags = merge(local.common_tags, {
    Name = "aws-waf-logs-api"
  })
}

resource "aws_wafv2_web_acl_logging_configuration" "api" {
  provider = aws.us-east-1

  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]
  resource_arn            = aws_wafv2_web_acl.api.arn
}
