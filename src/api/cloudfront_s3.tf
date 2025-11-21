resource "aws_s3_bucket" "docs" {
  bucket        = var.domain_subdomain
  force_destroy = true

  tags = {
    Name = "${var.domain_subdomain}-docs"
  }
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

resource "aws_s3_object" "index_html" {
  bucket       = aws_s3_bucket.docs.id
  key          = "index.html"
  source       = "${path.module}/files/index.html"
  content_type = "text/html"
  etag         = filemd5("${path.module}/files/index.html")
}

resource "aws_s3_object" "not_found_html" {
  bucket       = aws_s3_bucket.docs.id
  key          = "404.html"
  source       = "${path.module}/files/404.html"
  content_type = "text/html"
  etag         = filemd5("${path.module}/files/404.html")
}

resource "aws_s3_object" "openapi_yml" {
  bucket       = aws_s3_bucket.docs.id
  key          = "openapi.yml"
  source       = "${path.module}/files/openapi.yml"
  content_type = "application/x-yaml"
  etag         = filemd5("${path.module}/files/openapi.yml")
}

resource "aws_cloudfront_origin_access_control" "s3" {
  name                              = "${var.domain_subdomain}-oac"
  description                       = "OAC for S3 docs bucket"
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

  tags = {
    Name = "ApiWafWebAcl"
  }
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
  comment = "Rewrites / to /index.html for S3 origin"
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
  comment             = "API Gateway + S3 docs distribution v2"
  default_root_object = ""
  aliases             = [var.domain_subdomain]
  web_acl_id          = aws_wafv2_web_acl.api.arn

  origin {
    domain_name         = "${aws_api_gateway_rest_api.main.id}.execute-api.${var.aws_region}.amazonaws.com"
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
    allowed_methods        = ["GET", "HEAD"]
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

  tags = {
    Name = "${var.domain_subdomain}-distribution"
  }

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
