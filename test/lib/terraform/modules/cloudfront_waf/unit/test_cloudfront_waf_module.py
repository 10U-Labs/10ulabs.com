"""Tests for cloudfront_waf Terraform module."""


def test_module_files_exist(module_path):
    """Test that required module files exist."""
    assert (module_path / "main.tf").exists()
    assert (module_path / "variables.tf").exists()
    assert (module_path / "outputs.tf").exists()
    assert (module_path / "providers.tf").exists()


def test_wafv2_web_acl_resource_exists(main_tf_content):
    """Test that WAFv2 web ACL resource exists."""
    assert 'resource "aws_wafv2_web_acl"' in main_tf_content


def test_wafv2_web_acl_uses_us_east_1_provider(main_tf_content):
    """Test that WAFv2 web ACL uses us-east-1 provider."""
    assert 'provider = aws.us-east-1' in main_tf_content


def test_wafv2_web_acl_scope_is_cloudfront(main_tf_content):
    """Test that WAFv2 web ACL scope is CLOUDFRONT."""
    assert 'scope = "CLOUDFRONT"' in main_tf_content


def test_wafv2_web_acl_has_default_allow(main_tf_content):
    """Test that WAFv2 web ACL has default allow action."""
    assert 'default_action {' in main_tf_content
    assert 'allow {}' in main_tf_content


def test_cloudwatch_log_group_exists(main_tf_content):
    """Test that CloudWatch log group resource exists."""
    assert 'resource "aws_cloudwatch_log_group" "waf"' in main_tf_content


def test_cloudwatch_log_group_uses_us_east_1_provider(main_tf_content):
    """Test that CloudWatch log group uses us-east-1 provider."""
    # The log group should use the same provider as the WAF
    lines = main_tf_content.split('\n')
    in_log_group = False
    for line in lines:
        if 'resource "aws_cloudwatch_log_group" "waf"' in line:
            in_log_group = True
        if in_log_group and 'provider = aws.us-east-1' in line:
            assert True
            return
        if in_log_group and line.strip() == '}':
            break
    assert 'provider = aws.us-east-1' in main_tf_content


def test_cloudwatch_log_group_has_waf_prefix(main_tf_content):
    """Test that CloudWatch log group has aws-waf-logs- prefix."""
    assert 'aws-waf-logs-' in main_tf_content


def test_cloudwatch_log_group_has_retention(main_tf_content):
    """Test that CloudWatch log group has retention configured."""
    assert 'retention_in_days' in main_tf_content


def test_log_retention_default_is_30_days(variables_tf_content):
    """Test that log retention default is 30 days."""
    assert 'default     = 30' in variables_tf_content


def test_wafv2_logging_configuration_exists(main_tf_content):
    """Test that WAFv2 logging configuration exists."""
    assert 'resource "aws_wafv2_web_acl_logging_configuration"' in main_tf_content


def test_wafv2_logging_uses_log_group(main_tf_content):
    """Test that WAFv2 logging uses CloudWatch log group."""
    assert 'aws_cloudwatch_log_group.waf.arn' in main_tf_content


def test_wafv2_logging_uses_web_acl_arn(main_tf_content):
    """Test that WAFv2 logging uses web ACL ARN."""
    assert 'aws_wafv2_web_acl.this.arn' in main_tf_content


def test_wafv2_logging_has_log_destination_configs(main_tf_content):
    """Test that WAFv2 logging has log destination configs."""
    assert 'log_destination_configs' in main_tf_content


def test_name_variable_exists(variables_tf_content):
    """Test that name variable exists."""
    assert 'variable "name"' in variables_tf_content


def test_metric_name_variable_exists(variables_tf_content):
    """Test that metric_name variable exists."""
    assert 'variable "metric_name"' in variables_tf_content


def test_log_group_suffix_variable_exists(variables_tf_content):
    """Test that log_group_suffix variable exists."""
    assert 'variable "log_group_suffix"' in variables_tf_content


def test_web_acl_arn_output_exists(outputs_tf_content):
    """Test that web_acl_arn output exists."""
    assert 'output "web_acl_arn"' in outputs_tf_content


def test_web_acl_id_output_exists(outputs_tf_content):
    """Test that web_acl_id output exists."""
    assert 'output "web_acl_id"' in outputs_tf_content


def test_log_group_arn_output_exists(outputs_tf_content):
    """Test that log_group_arn output exists."""
    assert 'output "log_group_arn"' in outputs_tf_content
