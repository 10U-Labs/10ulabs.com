"""Tests for CloudFront and S3 Terraform configuration."""


def test_cloudfront_s3_terraform_file_exists(website_src_path):
    """Test that cloudfront_s3.tf file exists."""
    assert (website_src_path / "cloudfront_s3.tf").exists()


def test_website_bucket_module_used(cloudfront_s3_tf_content):
    """Test that website_bucket module is used."""
    assert 'module "website_bucket"' in cloudfront_s3_tf_content


def test_website_bucket_module_source(cloudfront_s3_tf_content):
    """Test that website_bucket module uses correct source."""
    assert 'source = "../../../lib/terraform/modules/s3_bucket"' in cloudfront_s3_tf_content


def test_website_bucket_versioning_disabled(cloudfront_s3_tf_content):
    """Test that website bucket versioning is disabled."""
    assert 'versioning_enabled  = false' in cloudfront_s3_tf_content


def test_website_waf_module_used(cloudfront_s3_tf_content):
    """Test that website_waf module is used."""
    assert 'module "website_waf"' in cloudfront_s3_tf_content


def test_website_waf_module_source(cloudfront_s3_tf_content):
    """Test that website_waf module uses correct source."""
    assert 'source = "../../../lib/terraform/modules/cloudfront_waf"' in cloudfront_s3_tf_content


def test_cloudfront_origin_access_control_exists(cloudfront_s3_tf_content):
    """Test that CloudFront origin access control exists."""
    resource = 'resource "aws_cloudfront_origin_access_control" "website"'
    assert resource in cloudfront_s3_tf_content


def test_s3_bucket_policy_exists(cloudfront_s3_tf_content):
    """Test that S3 bucket policy exists."""
    assert 'resource "aws_s3_bucket_policy" "website"' in cloudfront_s3_tf_content


def test_cloudfront_cache_policy_exists(cloudfront_s3_tf_content):
    """Test that CloudFront cache policy exists."""
    resource = 'resource "aws_cloudfront_cache_policy" "website"'
    assert resource in cloudfront_s3_tf_content


def test_cloudfront_function_spa_routing_exists(cloudfront_s3_tf_content):
    """Test that CloudFront function for SPA routing exists."""
    assert 'resource "aws_cloudfront_function" "spa_routing"' in cloudfront_s3_tf_content


def test_cloudfront_distribution_exists(cloudfront_s3_tf_content):
    """Test that CloudFront distribution exists."""
    resource = 'resource "aws_cloudfront_distribution" "website"'
    assert resource in cloudfront_s3_tf_content


def test_cloudfront_distribution_uses_certificate(cloudfront_s3_tf_content):
    """Test that CloudFront distribution uses ACM certificate."""
    assert 'acm_certificate_arn' in cloudfront_s3_tf_content


def test_cloudfront_distribution_uses_waf(cloudfront_s3_tf_content):
    """Test that CloudFront distribution uses WAF."""
    assert 'web_acl_id' in cloudfront_s3_tf_content


def test_cloudfront_origin_request_policy_data_source_exists(cloudfront_s3_tf_content):
    """Test that CloudFront origin request policy data source exists."""
    assert 'data "aws_cloudfront_origin_request_policy"' in cloudfront_s3_tf_content


def test_cloudfront_distribution_has_logging_config(cloudfront_s3_tf_content):
    """Test that CloudFront distribution has logging config."""
    assert 'logging_config {' in cloudfront_s3_tf_content


def test_cloudfront_logging_uses_central_logs_bucket(cloudfront_s3_tf_content):
    """Test that CloudFront logging uses central logs bucket."""
    assert 'local.name_for_central_logs' in cloudfront_s3_tf_content


def test_cloudfront_logging_has_prefix(cloudfront_s3_tf_content):
    """Test that CloudFront logging has correct prefix."""
    assert 'cloudfront-logs/website/' in cloudfront_s3_tf_content


def test_cloudfront_logging_excludes_cookies(cloudfront_s3_tf_content):
    """Test that CloudFront logging excludes cookies."""
    assert 'include_cookies = false' in cloudfront_s3_tf_content


def test_cloudfront_logging_bucket_uses_s3_domain(cloudfront_s3_tf_content):
    """Test that CloudFront logging bucket uses S3 domain."""
    assert '.s3.amazonaws.com' in cloudfront_s3_tf_content


def test_cloudfront_custom_error_response_403(cloudfront_s3_tf_content):
    """Test that CloudFront has custom 403 error response."""
    assert 'error_code         = 403' in cloudfront_s3_tf_content


def test_cloudfront_custom_error_response_404(cloudfront_s3_tf_content):
    """Test that CloudFront has custom 404 error response."""
    assert 'error_code         = 404' in cloudfront_s3_tf_content


def test_cloudfront_spa_routing_returns_index_html(cloudfront_s3_tf_content):
    """Test that CloudFront SPA routing returns index.html."""
    assert '/index.html' in cloudfront_s3_tf_content


def test_cloudfront_distribution_has_www_alias(cloudfront_s3_tf_content):
    """Test that CloudFront distribution has www alias."""
    assert 'local.www_fqdn' in cloudfront_s3_tf_content


def test_cloudfront_distribution_has_apex_alias(cloudfront_s3_tf_content):
    """Test that CloudFront distribution has apex alias."""
    assert 'local.apex_fqdn' in cloudfront_s3_tf_content


def test_cloudfront_function_redirects_apex_to_www(cloudfront_s3_tf_content):
    """Test that CloudFront function redirects apex to www."""
    assert 'statusCode: 301' in cloudfront_s3_tf_content


def test_cloudfront_function_checks_host_header(cloudfront_s3_tf_content):
    """Test that CloudFront function checks host header."""
    assert 'request.headers.host.value' in cloudfront_s3_tf_content


def test_cloudfront_response_headers_policy_exists(cloudfront_s3_tf_content):
    """Test that CloudFront response headers policy exists."""
    resource = 'resource "aws_cloudfront_response_headers_policy" "website"'
    assert resource in cloudfront_s3_tf_content


def test_cloudfront_response_headers_policy_has_hsts(cloudfront_s3_tf_content):
    """Test that CloudFront response headers policy has HSTS."""
    assert 'strict_transport_security {' in cloudfront_s3_tf_content


def test_cloudfront_distribution_uses_response_headers_policy(cloudfront_s3_tf_content):
    """Test that CloudFront distribution uses response headers policy."""
    assert 'response_headers_policy_id' in cloudfront_s3_tf_content


def test_cloudfront_function_handles_rack_designer_path(cloudfront_s3_tf_content):
    """Test that CloudFront function handles rack-designer path."""
    assert "uri === '/rack-designer'" in cloudfront_s3_tf_content


def test_cloudfront_function_redirects_rack_designer_to_trailing_slash(cloudfront_s3_tf_content):
    """Test that CloudFront function redirects rack-designer to trailing slash."""
    assert "'/rack-designer/'" in cloudfront_s3_tf_content


def test_cloudfront_function_handles_rack_designer_trailing_slash(cloudfront_s3_tf_content):
    """Test that CloudFront function handles rack-designer trailing slash."""
    assert "uri === '/rack-designer/'" in cloudfront_s3_tf_content


def test_cloudfront_function_rewrites_rack_designer_to_index(cloudfront_s3_tf_content):
    """Test that CloudFront function rewrites rack-designer to index.html."""
    assert "request.uri = '/rack-designer/index.html'" in cloudfront_s3_tf_content


def test_cloudfront_function_passes_through_rack_designer_subpaths(cloudfront_s3_tf_content):
    """Test that CloudFront function passes through rack-designer subpaths."""
    assert "uri.startsWith('/rack-designer/')" in cloudfront_s3_tf_content


def test_cloudfront_function_matches_config_hash(cloudfront_s3_tf_content):
    """Test that CloudFront function matches config hash pattern."""
    assert "uri.match(/^\\/rack-designer\\/[A-Z0-9]{8,9}$/)" in cloudfront_s3_tf_content


def test_cloudfront_function_rewrites_config_hash_to_index(cloudfront_s3_tf_content):
    """Test that CloudFront function rewrites config hash to index."""
    assert "configHashMatch" in cloudfront_s3_tf_content
