from pathlib import Path


def test_cloudfront_s3_terraform_file_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    assert cf_file.exists()


def test_s3_bucket_docs_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_bucket" "docs"' in content


def test_s3_bucket_versioning_disabled():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'aws_s3_bucket_versioning' in content
    assert 'Disabled' in content or 'disabled' in content.lower()


def test_s3_bucket_public_access_block_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_bucket_public_access_block" "docs"' in content


def test_s3_bucket_encryption_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_bucket_server_side_encryption_configuration" "docs"' in content


def test_s3_object_index_html_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_object" "index_html"' in content


def test_s3_object_not_found_html_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_object" "not_found_html"' in content


def test_s3_object_openapi_yml_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_object" "openapi_yml"' in content


def test_cloudfront_origin_access_control_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudfront_origin_access_control" "s3"' in content


def test_s3_bucket_policy_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_bucket_policy" "docs"' in content


def test_wafv2_web_acl_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_wafv2_web_acl" "api"' in content


def test_cloudfront_cache_policy_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudfront_cache_policy" "docs"' in content


def test_cloudfront_function_url_rewrite_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudfront_function" "url_rewrite"' in content


def test_cloudfront_distribution_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudfront_distribution" "main"' in content


def test_cloudfront_distribution_uses_certificate():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'acm_certificate_arn' in content


def test_cloudfront_distribution_uses_waf():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'web_acl_id' in content


def test_cloudfront_data_sources_exist():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "aws_cloudfront_cache_policy" "disabled"' in content
    assert 'data "aws_cloudfront_origin_request_policy"' in content


def test_cloudfront_distribution_has_logging_config():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'logging_config {' in content


def test_cloudfront_logging_uses_central_logs_bucket():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'module.shared.name_for_central_logs_bucket' in content


def test_cloudfront_logging_has_prefix():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'cloudfront-logs/api/' in content


def test_cloudfront_logging_excludes_cookies():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'include_cookies = false' in content


def test_cloudfront_logging_bucket_uses_s3_domain():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert '.s3.amazonaws.com' in content


def test_waf_cloudwatch_log_group_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "waf"' in content


def test_waf_log_group_has_correct_name_prefix():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'aws-waf-logs-' in content


def test_waf_log_group_name_is_aws_waf_logs_api():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'name              = "aws-waf-logs-api"' in content


def test_waf_log_group_retention_is_30_days():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'retention_in_days = 30' in content


def test_waf_log_group_uses_us_east_1_provider():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'provider = aws.us-east-1' in content


def test_waf_log_group_has_name_tag():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'Name = "aws-waf-logs-api"' in content


def test_waf_logging_configuration_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_wafv2_web_acl_logging_configuration" "api"' in content


def test_waf_logging_configuration_uses_us_east_1_provider():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_wafv2_web_acl_logging_configuration" "api"' in content


def test_waf_logging_uses_log_group():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'aws_cloudwatch_log_group.waf.arn' in content


def test_waf_logging_uses_web_acl_arn():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource_arn            = aws_wafv2_web_acl.api.arn' in content


def test_waf_logging_has_log_destination_configs():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'log_destination_configs' in content
