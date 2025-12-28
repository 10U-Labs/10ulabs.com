"""Tests for CloudFront and S3 Terraform configuration."""
import re


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
    pattern = r'versioning_enabled\s*=\s*false'
    assert re.search(pattern, cloudfront_s3_tf_content), (
        "Expected versioning_enabled = false in website_bucket module"
    )


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


def test_cloudfront_distribution_exists(cloudfront_s3_tf_content):
    """Test that CloudFront distribution exists."""
    resource = 'resource "aws_cloudfront_distribution" "website"'
    assert resource in cloudfront_s3_tf_content


def test_cloudfront_distribution_uses_certificate(cloudfront_s3_tf_content):
    """Test that CloudFront distribution uses ACM certificate."""
    pattern = r'acm_certificate_arn\s*=\s*aws_acm_certificate\.'
    assert re.search(pattern, cloudfront_s3_tf_content), (
        "Expected acm_certificate_arn assignment in viewer_certificate block"
    )


def test_cloudfront_distribution_uses_waf(cloudfront_s3_tf_content):
    """Test that CloudFront distribution uses WAF."""
    pattern = r'web_acl_id\s*=\s*module\.website_waf\.'
    assert re.search(pattern, cloudfront_s3_tf_content), (
        "Expected web_acl_id assignment referencing website_waf module"
    )


def test_cloudfront_origin_request_policy_data_source_exists(cloudfront_s3_tf_content):
    """Test that CloudFront origin request policy data source exists."""
    assert 'data "aws_cloudfront_origin_request_policy"' in cloudfront_s3_tf_content


def test_cloudfront_distribution_has_logging_config(cloudfront_s3_tf_content):
    """Test that CloudFront distribution has logging config."""
    assert 'logging_config {' in cloudfront_s3_tf_content


def test_cloudfront_logging_uses_central_logs_bucket(cloudfront_s3_tf_content):
    """Test that CloudFront logging uses central logs bucket."""
    pattern = r'bucket\s*=\s*"\$\{local\.name_for_central_logs\}'
    assert re.search(pattern, cloudfront_s3_tf_content), (
        "Expected bucket assignment using local.name_for_central_logs in logging_config"
    )


def test_cloudfront_logging_has_prefix(cloudfront_s3_tf_content):
    """Test that CloudFront logging has correct prefix."""
    pattern = r'prefix\s*=\s*"cloudfront-logs/website/"'
    assert re.search(pattern, cloudfront_s3_tf_content), (
        "Expected prefix = \"cloudfront-logs/website/\" in logging_config"
    )


def test_cloudfront_logging_excludes_cookies(cloudfront_s3_tf_content):
    """Test that CloudFront logging excludes cookies."""
    pattern = r'include_cookies\s*=\s*false'
    assert re.search(pattern, cloudfront_s3_tf_content), (
        "Expected include_cookies = false in logging_config"
    )


def test_cloudfront_logging_bucket_uses_s3_domain(cloudfront_s3_tf_content):
    """Test that CloudFront logging bucket uses S3 domain."""
    pattern = r'bucket\s*=\s*"[^"]*\.s3\.amazonaws\.com"'
    assert re.search(pattern, cloudfront_s3_tf_content), (
        "Expected bucket assignment with .s3.amazonaws.com domain"
    )


def test_cloudfront_custom_error_response_403(cloudfront_s3_tf_content):
    """Test that CloudFront has custom 403 error response."""
    pattern = r'error_code\s*=\s*403'
    assert re.search(pattern, cloudfront_s3_tf_content), (
        "Expected error_code = 403 in custom_error_response"
    )


def test_cloudfront_custom_error_response_404(cloudfront_s3_tf_content):
    """Test that CloudFront has custom 404 error response."""
    pattern = r'error_code\s*=\s*404'
    assert re.search(pattern, cloudfront_s3_tf_content), (
        "Expected error_code = 404 in custom_error_response"
    )


def test_cloudfront_spa_routing_returns_home_index_html(cloudfront_s3_tf_content):
    """Test that CloudFront SPA routing returns /home/index.html."""
    pattern = r'response_page_path\s*=\s*"/home/index\.html"'
    assert re.search(pattern, cloudfront_s3_tf_content), (
        "Expected response_page_path = \"/home/index.html\" in custom_error_response"
    )


def test_cloudfront_distribution_has_www_alias(cloudfront_s3_tf_content):
    """Test that CloudFront distribution has www alias."""
    pattern = r'aliases\s*=\s*\[.*local\.www_fqdn'
    assert re.search(pattern, cloudfront_s3_tf_content, re.DOTALL), (
        "Expected aliases list containing local.www_fqdn"
    )


def test_cloudfront_distribution_has_apex_alias(cloudfront_s3_tf_content):
    """Test that CloudFront distribution has apex alias."""
    pattern = r'aliases\s*=\s*\[.*local\.apex_fqdn'
    assert re.search(pattern, cloudfront_s3_tf_content, re.DOTALL), (
        "Expected aliases list containing local.apex_fqdn"
    )


def test_cloudfront_response_headers_policy_exists(cloudfront_s3_tf_content):
    """Test that CloudFront response headers policy exists."""
    resource = 'resource "aws_cloudfront_response_headers_policy" "website"'
    assert resource in cloudfront_s3_tf_content


def test_cloudfront_response_headers_policy_has_hsts(cloudfront_s3_tf_content):
    """Test that CloudFront response headers policy has HSTS."""
    assert 'strict_transport_security {' in cloudfront_s3_tf_content


def test_cloudfront_distribution_uses_response_headers_policy(cloudfront_s3_tf_content):
    """Test that CloudFront distribution uses response headers policy."""
    pattern = r'response_headers_policy_id\s*=\s*aws_cloudfront_response_headers_policy\.'
    assert re.search(pattern, cloudfront_s3_tf_content), (
        "Expected response_headers_policy_id assignment in default_cache_behavior"
    )


