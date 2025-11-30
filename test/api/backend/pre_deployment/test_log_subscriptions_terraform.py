from pathlib import Path


def test_log_subscriptions_terraform_file_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    assert log_subscriptions_file.exists()


def test_health_handler_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "health_handler"' in content


def test_catchall_handler_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "catchall_handler"' in content


def test_runners_handler_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "runners_handler"' in content


def test_v1_handler_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "v1_handler"' in content


def test_circuit_breaker_remediation_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "circuit_breaker_remediation"' in content


def test_dlq_reprocessor_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "dlq_reprocessor"' in content


def test_circuit_breaker_recovery_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "circuit_breaker_recovery"' in content


def test_api_gateway_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "api_gateway"' in content


def test_ecs_runner_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "ecs_runner"' in content


def test_health_handler_subscription_has_empty_filter_pattern():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'name            = "health-handler-to-firehose"' in content


def test_catchall_handler_subscription_has_name():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'name            = "catchall-handler-to-firehose"' in content


def test_runners_handler_subscription_has_name():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'name            = "runners-handler-to-firehose"' in content


def test_v1_handler_subscription_has_name():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'name            = "v1-handler-to-firehose"' in content


def test_circuit_breaker_remediation_subscription_has_name():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'name            = "circuit-breaker-remediation-to-firehose"' in content


def test_dlq_reprocessor_subscription_has_name():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'name            = "dlq-reprocessor-to-firehose"' in content


def test_circuit_breaker_recovery_subscription_has_name():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'name            = "circuit-breaker-recovery-to-firehose"' in content


def test_api_gateway_subscription_has_name():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'name            = "api-gateway-to-firehose"' in content


def test_ecs_runner_subscription_has_name():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'name            = "ecs-runner-to-firehose"' in content


def test_subscriptions_use_firehose_destination():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'destination_arn = aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn' in content


def test_subscriptions_use_cloudwatch_logs_firehose_role():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'role_arn        = aws_iam_role.cloudwatch_logs_firehose.arn' in content


def test_subscriptions_use_empty_filter_pattern():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'filter_pattern  = ""' in content


def test_waf_subscription_filter_exists():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "waf"' in content


def test_waf_subscription_has_name():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'name            = "waf-to-firehose"' in content


def test_waf_subscription_uses_waf_log_group():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    assert 'aws_cloudwatch_log_group.waf.name' in content


def test_waf_subscription_uses_firehose_destination():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    waf_section_start = content.find('resource "aws_cloudwatch_log_subscription_filter" "waf"')
    waf_section = content[waf_section_start:waf_section_start + 500]
    assert 'aws_kinesis_firehose_delivery_stream.cloudwatch_logs.arn' in waf_section


def test_waf_subscription_uses_cloudwatch_logs_firehose_role():
    log_subscriptions_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "log_subscriptions.tf"
    with open(log_subscriptions_file, encoding="utf-8") as f:
        content = f.read()
    waf_section_start = content.find('resource "aws_cloudwatch_log_subscription_filter" "waf"')
    waf_section = content[waf_section_start:waf_section_start + 500]
    assert 'aws_iam_role.cloudwatch_logs_firehose.arn' in waf_section
