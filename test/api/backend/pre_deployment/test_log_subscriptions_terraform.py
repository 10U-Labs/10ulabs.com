from pathlib import Path


def test_log_subscriptions_terraform_file_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    file_exists = log_subscriptions_file.exists()
    assert file_exists


def test_health_handler_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    contains_filter = 'resource "aws_cloudwatch_log_subscription_filter" "health_handler"' in content
    assert contains_filter


def test_catchall_handler_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    contains_filter = 'resource "aws_cloudwatch_log_subscription_filter" "catchall_handler"' in content
    assert contains_filter


def test_api_gateway_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    contains_filter = 'resource "aws_cloudwatch_log_subscription_filter" "api_gateway"' in content
    assert contains_filter


def test_health_handler_subscription_has_empty_filter_pattern():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    has_name = 'name            = "health-handler-to-firehose"' in content
    assert has_name


def test_catchall_handler_subscription_has_name():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    has_name = 'name            = "catchall-handler-to-firehose"' in content
    assert has_name


def test_api_gateway_subscription_has_name():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    has_name = 'name            = "api-gateway-to-firehose"' in content
    assert has_name


def test_subscriptions_use_firehose_destination():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    uses_firehose_destination = 'destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn' in content
    assert uses_firehose_destination


def test_subscriptions_use_cloudwatch_logs_firehose_role():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    uses_firehose_role = 'role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn' in content
    assert uses_firehose_role


def test_subscriptions_use_empty_filter_pattern():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    uses_empty_filter = 'filter_pattern  = ""' in content
    assert uses_empty_filter


def test_waf_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    contains_filter = 'resource "aws_cloudwatch_log_subscription_filter" "waf"' in content
    assert contains_filter


def test_waf_subscription_has_name():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    has_name = 'name            = "waf-to-firehose"' in content
    assert has_name


def test_waf_subscription_uses_waf_log_group():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    uses_waf_log_group = 'aws_cloudwatch_log_group.waf.name' in content
    assert uses_waf_log_group


def test_waf_subscription_uses_firehose_destination():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    waf_section_start = content.find('resource "aws_cloudwatch_log_subscription_filter" "waf"')
    waf_section = content[waf_section_start:waf_section_start + 500]
    uses_firehose = 'aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn' in waf_section
    assert uses_firehose


def test_waf_subscription_uses_cloudwatch_logs_firehose_role():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    waf_section_start = content.find('resource "aws_cloudwatch_log_subscription_filter" "waf"')
    waf_section = content[waf_section_start:waf_section_start + 500]
    uses_firehose_role = 'aws_iam_role.cloudwatch_logs_firehose.arn' in waf_section
    assert uses_firehose_role
