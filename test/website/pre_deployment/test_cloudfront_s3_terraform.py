from pathlib import Path


def test_cloudfront_s3_terraform_file_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    assert cf_file.exists()


def test_s3_bucket_website_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_bucket" "website"' in content


def test_s3_bucket_versioning_resource_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'aws_s3_bucket_versioning' in content


def test_s3_bucket_versioning_disabled():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'Disabled' in content


def test_s3_bucket_public_access_block_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_bucket_public_access_block" "website"' in content


def test_s3_bucket_encryption_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_bucket_server_side_encryption_configuration" "website"' in content


def test_cloudfront_origin_access_control_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudfront_origin_access_control" "website"' in content


def test_s3_bucket_policy_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_s3_bucket_policy" "website"' in content


def test_wafv2_web_acl_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_wafv2_web_acl" "website"' in content


def test_cloudfront_cache_policy_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudfront_cache_policy" "website"' in content


def test_cloudfront_function_spa_routing_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudfront_function" "spa_routing"' in content


def test_cloudfront_distribution_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudfront_distribution" "website"' in content


def test_cloudfront_distribution_uses_certificate():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'acm_certificate_arn' in content


def test_cloudfront_distribution_uses_waf():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'web_acl_id' in content


def test_cloudfront_origin_request_policy_data_source_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "aws_cloudfront_origin_request_policy"' in content


def test_cloudfront_distribution_has_logging_config():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'logging_config {' in content


def test_cloudfront_logging_uses_central_logs_bucket():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'local.name_for_central_logs' in content


def test_cloudfront_logging_has_prefix():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'cloudfront-logs/website/' in content


def test_cloudfront_logging_excludes_cookies():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'include_cookies = false' in content


def test_cloudfront_logging_bucket_uses_s3_domain():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert '.s3.amazonaws.com' in content


def test_waf_cloudwatch_log_group_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "waf"' in content


def test_waf_log_group_has_correct_name_prefix():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'aws-waf-logs-' in content


def test_waf_log_group_name_is_aws_waf_logs_website():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'name              = "aws-waf-logs-website"' in content


def test_waf_log_group_retention_is_30_days():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'retention_in_days = 30' in content


def test_waf_log_group_uses_us_east_1_provider():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'provider = aws.us-east-1' in content


def test_waf_log_group_has_name_tag():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'Name = "aws-waf-logs-website"' in content


def test_waf_logging_configuration_exists():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_wafv2_web_acl_logging_configuration" "website"' in content


def test_waf_logging_uses_log_group():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'aws_cloudwatch_log_group.waf.arn' in content


def test_waf_logging_uses_web_acl_arn():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource_arn            = aws_wafv2_web_acl.website.arn' in content


def test_waf_logging_has_log_destination_configs():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'log_destination_configs' in content


def test_cloudfront_custom_error_response_403():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'error_code         = 403' in content


def test_cloudfront_custom_error_response_404():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'error_code         = 404' in content


def test_cloudfront_spa_routing_returns_index_html():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert '/index.html' in content


def test_cloudfront_distribution_has_www_alias():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'local.www_fqdn' in content


def test_cloudfront_distribution_has_apex_alias():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'local.apex_fqdn' in content


def test_cloudfront_function_redirects_apex_to_www():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'statusCode: 301' in content


def test_cloudfront_function_checks_host_header():
    cf_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "cloudfront_s3.tf"
    with open(cf_file, encoding="utf-8") as f:
        content = f.read()
    assert 'request.headers.host.value' in content
