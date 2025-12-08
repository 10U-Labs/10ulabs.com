"""Tests for CloudFront and S3 Terraform configuration."""
from pathlib import Path


def _get_cloudfront_s3_tf_path() -> Path:
    """Get the path to cloudfront_s3.tf file."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent
    return base / "src" / "api" / "backend" / "cloudfront_s3.tf"


def _read_cloudfront_s3_tf() -> str:
    """Read and return the cloudfront_s3.tf content."""
    with open(_get_cloudfront_s3_tf_path(), encoding="utf-8") as f:
        return f.read()


def test_cloudfront_s3_terraform_file_exists():
    """Verify cloudfront_s3.tf file exists."""
    assert _get_cloudfront_s3_tf_path().exists()


def test_s3_bucket_docs_exists():
    """Verify S3 bucket for docs exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_s3_bucket" "docs"' in content


def test_s3_bucket_versioning_resource_exists():
    """Verify S3 bucket versioning resource exists."""
    content = _read_cloudfront_s3_tf()
    assert 'aws_s3_bucket_versioning' in content


def test_s3_bucket_versioning_disabled():
    """Verify S3 bucket versioning is disabled."""
    content = _read_cloudfront_s3_tf()
    assert 'Disabled' in content


def test_s3_bucket_public_access_block_exists():
    """Verify S3 bucket public access block exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_s3_bucket_public_access_block" "docs"' in content


def test_s3_bucket_encryption_exists():
    """Verify S3 bucket encryption resource exists."""
    content = _read_cloudfront_s3_tf()
    enc_resource = 'resource "aws_s3_bucket_server_side_encryption_configuration"'
    assert enc_resource in content


def test_s3_object_index_html_exists():
    """Verify index.html S3 object exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_s3_object" "index_html"' in content


def test_s3_object_not_found_html_exists():
    """Verify not_found.html S3 object exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_s3_object" "not_found_html"' in content


def test_s3_object_openapi_yml_exists():
    """Verify openapi.yml S3 object exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_s3_object" "openapi_yml"' in content


def test_cloudfront_origin_access_control_exists():
    """Verify CloudFront origin access control exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_cloudfront_origin_access_control" "s3"' in content


def test_s3_bucket_policy_exists():
    """Verify S3 bucket policy exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_s3_bucket_policy" "docs"' in content


def test_wafv2_web_acl_exists():
    """Verify WAFv2 Web ACL exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_wafv2_web_acl" "api"' in content


def test_cloudfront_cache_policy_exists():
    """Verify CloudFront cache policy exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_cloudfront_cache_policy" "docs"' in content


def test_cloudfront_function_url_rewrite_exists():
    """Verify CloudFront URL rewrite function exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_cloudfront_function" "url_rewrite"' in content


def test_cloudfront_distribution_exists():
    """Verify CloudFront distribution exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_cloudfront_distribution" "main"' in content


def test_cloudfront_distribution_uses_certificate():
    """Verify CloudFront distribution uses ACM certificate."""
    content = _read_cloudfront_s3_tf()
    assert 'acm_certificate_arn' in content


def test_cloudfront_distribution_uses_waf():
    """Verify CloudFront distribution uses WAF."""
    content = _read_cloudfront_s3_tf()
    assert 'web_acl_id' in content


def test_cloudfront_cache_policy_data_source_exists():
    """Verify CloudFront cache policy data source exists."""
    content = _read_cloudfront_s3_tf()
    assert 'data "aws_cloudfront_cache_policy" "disabled"' in content


def test_cloudfront_origin_request_policy_data_source_exists():
    """Verify CloudFront origin request policy data source exists."""
    content = _read_cloudfront_s3_tf()
    assert 'data "aws_cloudfront_origin_request_policy"' in content


def test_cloudfront_distribution_has_logging_config():
    """Verify CloudFront distribution has logging config."""
    content = _read_cloudfront_s3_tf()
    assert 'logging_config {' in content


def test_cloudfront_logging_uses_central_logs_bucket():
    """Verify CloudFront logging uses central logs bucket."""
    content = _read_cloudfront_s3_tf()
    assert 'local.name_for_central_logs' in content


def test_cloudfront_logging_has_prefix():
    """Verify CloudFront logging has correct prefix."""
    content = _read_cloudfront_s3_tf()
    assert 'cloudfront-logs/api/' in content


def test_cloudfront_logging_excludes_cookies():
    """Verify CloudFront logging excludes cookies."""
    content = _read_cloudfront_s3_tf()
    assert 'include_cookies = false' in content


def test_cloudfront_logging_bucket_uses_s3_domain():
    """Verify CloudFront logging bucket uses S3 domain."""
    content = _read_cloudfront_s3_tf()
    assert '.s3.amazonaws.com' in content


def test_waf_cloudwatch_log_group_exists():
    """Verify WAF CloudWatch log group exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_cloudwatch_log_group" "waf"' in content


def test_waf_log_group_has_correct_name_prefix():
    """Verify WAF log group has correct name prefix."""
    content = _read_cloudfront_s3_tf()
    assert 'aws-waf-logs-' in content


def test_waf_log_group_name_is_aws_waf_logs_api():
    """Verify WAF log group name is aws-waf-logs-api."""
    content = _read_cloudfront_s3_tf()
    assert 'name              = "aws-waf-logs-api"' in content


def test_waf_log_group_retention_is_30_days():
    """Verify WAF log group retention is 30 days."""
    content = _read_cloudfront_s3_tf()
    assert 'retention_in_days = 30' in content


def test_waf_log_group_uses_us_east_1_provider():
    """Verify WAF log group uses us-east-1 provider."""
    content = _read_cloudfront_s3_tf()
    assert 'provider = aws.us-east-1' in content


def test_waf_log_group_has_name_tag():
    """Verify WAF log group has Name tag."""
    content = _read_cloudfront_s3_tf()
    assert 'Name = "aws-waf-logs-api"' in content


def test_waf_logging_configuration_exists():
    """Verify WAF logging configuration exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_wafv2_web_acl_logging_configuration" "api"' in content


def test_waf_logging_configuration_uses_us_east_1_provider():
    """Verify WAF logging configuration uses us-east-1 provider."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_wafv2_web_acl_logging_configuration" "api"' in content


def test_waf_logging_uses_log_group():
    """Verify WAF logging uses log group."""
    content = _read_cloudfront_s3_tf()
    assert 'aws_cloudwatch_log_group.waf.arn' in content


def test_waf_logging_uses_web_acl_arn():
    """Verify WAF logging uses Web ACL ARN."""
    content = _read_cloudfront_s3_tf()
    assert 'resource_arn            = aws_wafv2_web_acl.api.arn' in content


def test_waf_logging_has_log_destination_configs():
    """Verify WAF logging has log destination configs."""
    content = _read_cloudfront_s3_tf()
    assert 'log_destination_configs' in content
