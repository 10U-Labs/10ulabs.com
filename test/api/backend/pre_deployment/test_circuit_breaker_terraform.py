from pathlib import Path


def test_circuit_breaker_terraform_file_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    assert cb_file.exists()


def test_sns_topic_circuit_breaker_alerts_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sns_topic" "circuit_breaker_alerts"' in content


def test_sns_topic_subscription_email_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sns_topic_subscription" "circuit_breaker_email"' in content


def test_cloudwatch_alarm_circuit_breaker_open_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_metric_alarm" "circuit_breaker_open"' in content


def test_cloudwatch_alarm_high_failures_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_metric_alarm" "circuit_breaker_high_failures"' in content


def test_cloudwatch_alarm_webhook_handler_errors_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_metric_alarm" "webhook_handler_errors"' in content


def test_cloudwatch_alarm_job_queue_dlq_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_metric_alarm" "job_queue_dlq_messages"' in content


def test_eventbridge_rule_remediation_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_rule" "circuit_breaker_remediation"' in content


def test_eventbridge_target_remediation_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_target" "circuit_breaker_remediation"' in content


def test_lambda_permission_remediation_eventbridge_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "circuit_breaker_remediation_eventbridge"' in content


def test_eventbridge_rule_dlq_reprocessor_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_rule" "dlq_reprocessor"' in content


def test_eventbridge_target_dlq_reprocessor_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_target" "dlq_reprocessor"' in content


def test_lambda_permission_dlq_reprocessor_eventbridge_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "dlq_reprocessor_eventbridge"' in content


def test_eventbridge_rule_recovery_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_rule" "circuit_breaker_recovery"' in content


def test_eventbridge_target_recovery_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_target" "circuit_breaker_recovery"' in content


def test_lambda_permission_recovery_eventbridge_exists():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "circuit_breaker_recovery_eventbridge"' in content


def test_alarms_have_alarm_actions():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'alarm_actions' in content


def test_alarms_send_to_sns_topic():
    cb_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "circuit_breaker.tf"
    with open(cb_file, encoding="utf-8") as f:
        content = f.read()
    assert 'aws_sns_topic.circuit_breaker_alerts.arn' in content
