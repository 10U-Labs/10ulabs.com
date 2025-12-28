"""Unit tests for test circuit breaker terraform."""
def test_sns_terraform_file_exists(runners_src_path):
    """Test sns terraform file exists."""
    sns_file = runners_src_path / "sns.tf"
    assert sns_file.exists()


def test_cloudwatch_terraform_file_exists(runners_src_path):
    """Test cloudwatch terraform file exists."""
    cloudwatch_file = runners_src_path / "cloudwatch.tf"
    assert cloudwatch_file.exists()


def test_eventbridge_terraform_file_exists(runners_src_path):
    """Test eventbridge terraform file exists."""
    eventbridge_file = runners_src_path / "eventbridge.tf"
    assert eventbridge_file.exists()


def test_sns_topic_circuit_breaker_alerts_exists(runners_src_path):
    """Test sns topic circuit breaker alerts exists."""
    sns_file = runners_src_path / "sns.tf"
    with open(sns_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sns_topic" "circuit_breaker_alerts"' in content


def test_sns_topic_subscription_email_exists(runners_src_path):
    """Test sns topic subscription email exists."""
    sns_file = runners_src_path / "sns.tf"
    with open(sns_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_sns_topic_subscription" "circuit_breaker_email"' in content


def test_cloudwatch_alarm_circuit_breaker_open_exists(runners_src_path):
    """Test cloudwatch alarm circuit breaker open exists."""
    cloudwatch_file = runners_src_path / "cloudwatch.tf"
    with open(cloudwatch_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_metric_alarm" "circuit_breaker_open"' in content


def test_cloudwatch_alarm_high_failures_exists(runners_src_path):
    """Test cloudwatch alarm high failures exists."""
    cloudwatch_file = runners_src_path / "cloudwatch.tf"
    with open(cloudwatch_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_metric_alarm" "circuit_breaker_high_failures"' in content


def test_cloudwatch_alarm_webhook_handler_errors_exists(runners_src_path):
    """Test cloudwatch alarm webhook handler errors exists."""
    cloudwatch_file = runners_src_path / "cloudwatch.tf"
    with open(cloudwatch_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_metric_alarm" "webhook_handler_errors"' in content


def test_eventbridge_rule_remediation_exists(runners_src_path):
    """Test eventbridge rule remediation exists."""
    eventbridge_file = runners_src_path / "eventbridge.tf"
    with open(eventbridge_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_rule" "circuit_breaker_remediation"' in content


def test_eventbridge_target_remediation_exists(runners_src_path):
    """Test eventbridge target remediation exists."""
    eventbridge_file = runners_src_path / "eventbridge.tf"
    with open(eventbridge_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_target" "circuit_breaker_remediation"' in content


def test_lambda_permission_remediation_eventbridge_exists(runners_src_path):
    """Test lambda permission remediation eventbridge exists."""
    eventbridge_file = runners_src_path / "eventbridge.tf"
    with open(eventbridge_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "circuit_breaker_remediation_eventbridge"' in content


def test_eventbridge_rule_dlq_reprocessor_exists(runners_src_path):
    """Test eventbridge rule dlq reprocessor exists."""
    eventbridge_file = runners_src_path / "eventbridge.tf"
    with open(eventbridge_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_rule" "dlq_reprocessor"' in content


def test_eventbridge_target_dlq_reprocessor_exists(runners_src_path):
    """Test eventbridge target dlq reprocessor exists."""
    eventbridge_file = runners_src_path / "eventbridge.tf"
    with open(eventbridge_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_target" "dlq_reprocessor"' in content


def test_lambda_permission_dlq_reprocessor_eventbridge_exists(runners_src_path):
    """Test lambda permission dlq reprocessor eventbridge exists."""
    eventbridge_file = runners_src_path / "eventbridge.tf"
    with open(eventbridge_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "dlq_reprocessor_eventbridge"' in content


def test_eventbridge_rule_recovery_exists(runners_src_path):
    """Test eventbridge rule recovery exists."""
    eventbridge_file = runners_src_path / "eventbridge.tf"
    with open(eventbridge_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_rule" "circuit_breaker_recovery"' in content


def test_eventbridge_target_recovery_exists(runners_src_path):
    """Test eventbridge target recovery exists."""
    eventbridge_file = runners_src_path / "eventbridge.tf"
    with open(eventbridge_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_event_target" "circuit_breaker_recovery"' in content


def test_lambda_permission_recovery_eventbridge_exists(runners_src_path):
    """Test lambda permission recovery eventbridge exists."""
    eventbridge_file = runners_src_path / "eventbridge.tf"
    with open(eventbridge_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_permission" "circuit_breaker_recovery_eventbridge"' in content


def test_alarms_have_alarm_actions(runners_src_path):
    """Test alarms have alarm actions."""
    cloudwatch_file = runners_src_path / "cloudwatch.tf"
    with open(cloudwatch_file, encoding="utf-8") as f:
        content = f.read()
    assert 'alarm_actions' in content


def test_alarms_send_to_sns_topic(runners_src_path):
    """Test alarms send to sns topic."""
    cloudwatch_file = runners_src_path / "cloudwatch.tf"
    with open(cloudwatch_file, encoding="utf-8") as f:
        content = f.read()
    assert 'aws_sns_topic.circuit_breaker_alerts.arn' in content
