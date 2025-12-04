"""Tests for log_subscriptions.tf Terraform configuration."""

from pathlib import Path


def _get_terraform_path() -> Path:
    """Get the path to log_subscriptions.tf file."""
    base = Path(__file__).parent.parent.parent.parent.parent
    return base / "src" / "api" / "backend" / "log_subscriptions.tf"


def test_log_subscriptions_terraform_file_exists():
    """Verify that log_subscriptions.tf file exists."""
    log_subscriptions_file = _get_terraform_path()
    file_exists = log_subscriptions_file.exists()
    assert file_exists


def test_health_handler_subscription_filter_exists():
    """Verify that health handler subscription filter exists."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    filter_resource = 'resource "aws_cloudwatch_log_subscription_filter" "health_handler"'
    assert filter_resource in content


def test_catchall_handler_subscription_filter_exists():
    """Verify that catchall handler subscription filter exists."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    filter_resource = 'resource "aws_cloudwatch_log_subscription_filter" "catchall_handler"'
    assert filter_resource in content


def test_api_gateway_subscription_filter_exists():
    """Verify that API Gateway subscription filter exists."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    filter_resource = 'resource "aws_cloudwatch_log_subscription_filter" "api_gateway"'
    assert filter_resource in content


def test_health_handler_subscription_has_empty_filter_pattern():
    """Verify that health handler subscription has correct name."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    has_name = 'name            = "health-handler-to-firehose"' in content
    assert has_name


def test_catchall_handler_subscription_has_name():
    """Verify that catchall handler subscription has correct name."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    has_name = 'name            = "catchall-handler-to-firehose"' in content
    assert has_name


def test_api_gateway_subscription_has_name():
    """Verify that API Gateway subscription has correct name."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    has_name = 'name            = "api-gateway-to-firehose"' in content
    assert has_name


def test_subscriptions_use_firehose_destination():
    """Verify that subscriptions use Firehose destination."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    destination_ref = 'destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn'
    assert destination_ref in content


def test_subscriptions_use_cloudwatch_logs_firehose_role():
    """Verify that subscriptions use CloudWatch Logs Firehose role."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    role_ref = 'role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn'
    assert role_ref in content


def test_subscriptions_use_empty_filter_pattern():
    """Verify that subscriptions use empty filter pattern."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    uses_empty_filter = 'filter_pattern  = ""' in content
    assert uses_empty_filter


def test_waf_subscription_filter_exists():
    """Verify that WAF subscription filter exists."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    filter_resource = 'resource "aws_cloudwatch_log_subscription_filter" "waf"'
    assert filter_resource in content


def test_waf_subscription_has_name():
    """Verify that WAF subscription has correct name."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    has_name = 'name            = "waf-to-firehose"' in content
    assert has_name


def test_waf_subscription_uses_waf_log_group():
    """Verify that WAF subscription uses WAF log group."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    uses_waf_log_group = 'aws_cloudwatch_log_group.waf.name' in content
    assert uses_waf_log_group


def test_waf_subscription_uses_firehose_destination():
    """Verify that WAF subscription uses Firehose destination."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    filter_start = 'resource "aws_cloudwatch_log_subscription_filter" "waf"'
    waf_section_start = content.find(filter_start)
    waf_section = content[waf_section_start:waf_section_start + 500]
    firehose_arn = 'aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn'
    assert firehose_arn in waf_section


def test_waf_subscription_uses_cloudwatch_logs_firehose_role():
    """Verify that WAF subscription uses CloudWatch Logs Firehose role."""
    with open(_get_terraform_path(), encoding="utf-8") as f:
        content = f.read()
    filter_start = 'resource "aws_cloudwatch_log_subscription_filter" "waf"'
    waf_section_start = content.find(filter_start)
    waf_section = content[waf_section_start:waf_section_start + 500]
    role_arn = 'aws_iam_role.cloudwatch_logs_firehose.arn'
    assert role_arn in waf_section
