def test_cloudfront_s3_terraform_file_exists(website_src_path):
    assert (website_src_path / "cloudfront_s3.tf").exists()


def test_s3_bucket_website_exists(cloudfront_s3_tf_content):
    assert 'resource "aws_s3_bucket" "website"' in cloudfront_s3_tf_content


def test_s3_bucket_versioning_resource_exists(cloudfront_s3_tf_content):
    assert 'aws_s3_bucket_versioning' in cloudfront_s3_tf_content


def test_s3_bucket_versioning_disabled(cloudfront_s3_tf_content):
    assert 'Disabled' in cloudfront_s3_tf_content


def test_s3_bucket_public_access_block_exists(cloudfront_s3_tf_content):
    assert 'resource "aws_s3_bucket_public_access_block" "website"' in cloudfront_s3_tf_content


def test_s3_bucket_encryption_exists(cloudfront_s3_tf_content):
    assert 'resource "aws_s3_bucket_server_side_encryption_configuration" "website"' in cloudfront_s3_tf_content


def test_cloudfront_origin_access_control_exists(cloudfront_s3_tf_content):
    assert 'resource "aws_cloudfront_origin_access_control" "website"' in cloudfront_s3_tf_content


def test_s3_bucket_policy_exists(cloudfront_s3_tf_content):
    assert 'resource "aws_s3_bucket_policy" "website"' in cloudfront_s3_tf_content


def test_wafv2_web_acl_exists(cloudfront_s3_tf_content):
    assert 'resource "aws_wafv2_web_acl" "website"' in cloudfront_s3_tf_content


def test_cloudfront_cache_policy_exists(cloudfront_s3_tf_content):
    assert 'resource "aws_cloudfront_cache_policy" "website"' in cloudfront_s3_tf_content


def test_cloudfront_function_spa_routing_exists(cloudfront_s3_tf_content):
    assert 'resource "aws_cloudfront_function" "spa_routing"' in cloudfront_s3_tf_content


def test_cloudfront_distribution_exists(cloudfront_s3_tf_content):
    assert 'resource "aws_cloudfront_distribution" "website"' in cloudfront_s3_tf_content


def test_cloudfront_distribution_uses_certificate(cloudfront_s3_tf_content):
    assert 'acm_certificate_arn' in cloudfront_s3_tf_content


def test_cloudfront_distribution_uses_waf(cloudfront_s3_tf_content):
    assert 'web_acl_id' in cloudfront_s3_tf_content


def test_cloudfront_origin_request_policy_data_source_exists(cloudfront_s3_tf_content):
    assert 'data "aws_cloudfront_origin_request_policy"' in cloudfront_s3_tf_content


def test_cloudfront_distribution_has_logging_config(cloudfront_s3_tf_content):
    assert 'logging_config {' in cloudfront_s3_tf_content


def test_cloudfront_logging_uses_central_logs_bucket(cloudfront_s3_tf_content):
    assert 'local.name_for_central_logs' in cloudfront_s3_tf_content


def test_cloudfront_logging_has_prefix(cloudfront_s3_tf_content):
    assert 'cloudfront-logs/website/' in cloudfront_s3_tf_content


def test_cloudfront_logging_excludes_cookies(cloudfront_s3_tf_content):
    assert 'include_cookies = false' in cloudfront_s3_tf_content


def test_cloudfront_logging_bucket_uses_s3_domain(cloudfront_s3_tf_content):
    assert '.s3.amazonaws.com' in cloudfront_s3_tf_content


def test_waf_cloudwatch_log_group_exists(cloudfront_s3_tf_content):
    assert 'resource "aws_cloudwatch_log_group" "waf"' in cloudfront_s3_tf_content


def test_waf_log_group_has_correct_name_prefix(cloudfront_s3_tf_content):
    assert 'aws-waf-logs-' in cloudfront_s3_tf_content


def test_waf_log_group_retention_is_30_days(cloudfront_s3_tf_content):
    assert 'retention_in_days = 30' in cloudfront_s3_tf_content


def test_waf_log_group_uses_us_east_1_provider(cloudfront_s3_tf_content):
    assert 'provider = aws.us-east-1' in cloudfront_s3_tf_content


def test_waf_logging_configuration_exists(cloudfront_s3_tf_content):
    assert 'resource "aws_wafv2_web_acl_logging_configuration" "website"' in cloudfront_s3_tf_content


def test_waf_logging_uses_log_group(cloudfront_s3_tf_content):
    assert 'aws_cloudwatch_log_group.waf.arn' in cloudfront_s3_tf_content


def test_waf_logging_uses_web_acl_arn(cloudfront_s3_tf_content):
    assert 'resource_arn            = aws_wafv2_web_acl.website.arn' in cloudfront_s3_tf_content


def test_waf_logging_has_log_destination_configs(cloudfront_s3_tf_content):
    assert 'log_destination_configs' in cloudfront_s3_tf_content


def test_cloudfront_custom_error_response_403(cloudfront_s3_tf_content):
    assert 'error_code         = 403' in cloudfront_s3_tf_content


def test_cloudfront_custom_error_response_404(cloudfront_s3_tf_content):
    assert 'error_code         = 404' in cloudfront_s3_tf_content


def test_cloudfront_spa_routing_returns_index_html(cloudfront_s3_tf_content):
    assert '/index.html' in cloudfront_s3_tf_content


def test_cloudfront_distribution_has_www_alias(cloudfront_s3_tf_content):
    assert 'local.www_fqdn' in cloudfront_s3_tf_content


def test_cloudfront_distribution_has_apex_alias(cloudfront_s3_tf_content):
    assert 'local.apex_fqdn' in cloudfront_s3_tf_content


def test_cloudfront_function_redirects_apex_to_www(cloudfront_s3_tf_content):
    assert 'statusCode: 301' in cloudfront_s3_tf_content


def test_cloudfront_function_checks_host_header(cloudfront_s3_tf_content):
    assert 'request.headers.host.value' in cloudfront_s3_tf_content


def test_cloudfront_response_headers_policy_exists(cloudfront_s3_tf_content):
    assert 'resource "aws_cloudfront_response_headers_policy" "website"' in cloudfront_s3_tf_content


def test_cloudfront_response_headers_policy_has_hsts(cloudfront_s3_tf_content):
    assert 'strict_transport_security {' in cloudfront_s3_tf_content


def test_cloudfront_distribution_uses_response_headers_policy(cloudfront_s3_tf_content):
    assert 'response_headers_policy_id' in cloudfront_s3_tf_content


def test_contact_api_origin_exists(cloudfront_s3_tf_content):
    assert 'origin_id   = "contact-api"' in cloudfront_s3_tf_content


def test_contact_api_origin_uses_lambda_function_url(cloudfront_s3_tf_content):
    assert 'aws_lambda_function_url.contact_handler.function_url' in cloudfront_s3_tf_content


def test_contact_api_origin_uses_https_only(cloudfront_s3_tf_content):
    assert 'origin_protocol_policy = "https-only"' in cloudfront_s3_tf_content


def test_contact_api_origin_uses_tls12(cloudfront_s3_tf_content):
    assert 'origin_ssl_protocols   = ["TLSv1.2"]' in cloudfront_s3_tf_content


def test_contact_cache_behavior_exists(cloudfront_s3_tf_content):
    assert 'ordered_cache_behavior {' in cloudfront_s3_tf_content


def test_contact_cache_behavior_path_pattern(cloudfront_s3_tf_content):
    assert 'path_pattern           = "/contact"' in cloudfront_s3_tf_content


def test_contact_cache_behavior_targets_contact_api(cloudfront_s3_tf_content):
    assert 'target_origin_id       = "contact-api"' in cloudfront_s3_tf_content


def test_contact_cache_behavior_allows_post(cloudfront_s3_tf_content):
    assert 'allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]' in cloudfront_s3_tf_content


def test_caching_disabled_policy_data_source_exists(cloudfront_s3_tf_content):
    assert 'data "aws_cloudfront_cache_policy" "caching_disabled"' in cloudfront_s3_tf_content


def test_caching_disabled_policy_uses_managed_policy(cloudfront_s3_tf_content):
    assert 'name = "Managed-CachingDisabled"' in cloudfront_s3_tf_content


def test_all_viewer_except_host_header_policy_exists(cloudfront_s3_tf_content):
    assert 'data "aws_cloudfront_origin_request_policy" "all_viewer_except_host_header"' in cloudfront_s3_tf_content


def test_all_viewer_except_host_header_uses_managed_policy(cloudfront_s3_tf_content):
    assert 'name = "Managed-AllViewerExceptHostHeader"' in cloudfront_s3_tf_content


def test_contact_cache_behavior_uses_caching_disabled(cloudfront_s3_tf_content):
    assert 'cache_policy_id          = data.aws_cloudfront_cache_policy.caching_disabled.id' in cloudfront_s3_tf_content


def test_contact_cache_behavior_uses_all_viewer_except_host_header(cloudfront_s3_tf_content):
    assert 'origin_request_policy_id = data.aws_cloudfront_origin_request_policy.all_viewer_except_host_header.id' in cloudfront_s3_tf_content
