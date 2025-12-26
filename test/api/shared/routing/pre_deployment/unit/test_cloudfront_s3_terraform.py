"""Tests for CloudFront and S3 Terraform configuration."""
from pathlib import Path


def _get_cloudfront_s3_tf_path() -> Path:
    """Get the path to cloudfront_s3.tf file."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent.parent
    return base / "src" / "api" / "shared" / "routing" / "cloudfront_s3.tf"


def _read_cloudfront_s3_tf() -> str:
    """Read and return the cloudfront_s3.tf content."""
    with open(_get_cloudfront_s3_tf_path(), encoding="utf-8") as f:
        return f.read()


def test_cloudfront_s3_terraform_file_exists():
    """Verify cloudfront_s3.tf file exists."""
    assert _get_cloudfront_s3_tf_path().exists()


def test_docs_bucket_module_exists():
    """Verify docs_bucket module is used for S3 bucket configuration."""
    content = _read_cloudfront_s3_tf()
    assert 'module "docs_bucket"' in content


def test_docs_bucket_module_uses_s3_bucket_source():
    """Verify docs_bucket module uses s3_bucket module source."""
    content = _read_cloudfront_s3_tf()
    assert 'source = "../../../../lib/terraform/modules/s3_bucket"' in content


def test_docs_bucket_module_versioning_disabled():
    """Verify docs_bucket module has versioning disabled."""
    content = _read_cloudfront_s3_tf()
    assert 'versioning_enabled  = false' in content


def test_docs_bucket_module_has_force_destroy():
    """Verify docs_bucket module has force_destroy enabled."""
    content = _read_cloudfront_s3_tf()
    assert 'force_destroy       = true' in content


def test_docs_bucket_module_has_central_logs_bucket():
    """Verify docs_bucket module has central_logs_bucket configured."""
    content = _read_cloudfront_s3_tf()
    assert 'central_logs_bucket = local.name_for_central_logs' in content


def test_s3_object_index_html_exists():
    """Verify index.html S3 object exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_s3_object" "index_html"' in content


def test_s3_object_not_found_html_exists():
    """Verify not_found.html S3 object exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_s3_object" "not_found_html"' in content


def test_s3_object_openapi_json_exists():
    """Verify openapi.json S3 object exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_s3_object" "openapi_json"' in content


def test_cloudfront_origin_access_control_exists():
    """Verify CloudFront origin access control exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_cloudfront_origin_access_control" "s3"' in content


def test_s3_bucket_policy_exists():
    """Verify S3 bucket policy exists."""
    content = _read_cloudfront_s3_tf()
    assert 'resource "aws_s3_bucket_policy" "docs"' in content


def test_api_waf_module_exists():
    """Verify api_waf module is used for WAF configuration."""
    content = _read_cloudfront_s3_tf()
    assert 'module "api_waf"' in content


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


def test_api_waf_module_uses_cloudfront_waf_source():
    """Verify api_waf module uses cloudfront_waf module source."""
    content = _read_cloudfront_s3_tf()
    assert 'source = "../../../../lib/terraform/modules/cloudfront_waf"' in content


def test_api_waf_module_uses_us_east_1_provider():
    """Verify api_waf module uses us-east-1 provider."""
    content = _read_cloudfront_s3_tf()
    assert 'aws.us-east-1 = aws.us-east-1' in content


def test_api_waf_module_has_name():
    """Verify api_waf module has name configured."""
    content = _read_cloudfront_s3_tf()
    assert 'name             = "ApiWafWebAcl"' in content


def test_api_waf_module_has_metric_name():
    """Verify api_waf module has metric_name configured."""
    content = _read_cloudfront_s3_tf()
    assert 'metric_name      = "ApiWafMetrics"' in content


def test_api_waf_module_has_log_group_suffix():
    """Verify api_waf module has log_group_suffix configured."""
    content = _read_cloudfront_s3_tf()
    assert 'log_group_suffix = "api"' in content
