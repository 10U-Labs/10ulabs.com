"""Unit tests for runners log group Terraform configuration.

This module tests:
- Log group retention values in lambda.tf
- Subscription filters in log_subscriptions.tf
"""

from repo_utils import extract_brace_block


def _get_log_group_section(content: str, log_group_name: str) -> str:
    """Extract the log group resource section from Terraform content."""
    resource_pattern = f'resource "aws_cloudwatch_log_group" "{log_group_name}"'
    start = content.find(resource_pattern)
    if start == -1:
        return ""
    brace_start = content.find('{', start)
    if brace_start == -1:
        return ""
    return extract_brace_block(content, brace_start)


# =============================================================================
# Log Group Retention Tests
# =============================================================================


def test_circuit_breaker_recovery_log_group_has_7_day_retention(runners_src_path):
    """Verify circuit_breaker_recovery log group has 7-day retention."""
    with open(runners_src_path / "lambda.tf", encoding="utf-8") as f:
        content = f.read()
    section = _get_log_group_section(content, "circuit_breaker_recovery")
    assert "retention_in_days = 7" in section


def test_circuit_breaker_remediation_log_group_has_7_day_retention(runners_src_path):
    """Verify circuit_breaker_remediation log group has 7-day retention."""
    with open(runners_src_path / "lambda.tf", encoding="utf-8") as f:
        content = f.read()
    section = _get_log_group_section(content, "circuit_breaker_remediation")
    assert "retention_in_days = 7" in section


def test_circuit_breaker_reset_log_group_has_7_day_retention(runners_src_path):
    """Verify circuit_breaker_reset log group has 7-day retention."""
    with open(runners_src_path / "lambda.tf", encoding="utf-8") as f:
        content = f.read()
    section = _get_log_group_section(content, "circuit_breaker_reset")
    assert "retention_in_days = 7" in section


def test_dlq_reprocessor_log_group_has_7_day_retention(runners_src_path):
    """Verify dlq_reprocessor log group has 7-day retention."""
    with open(runners_src_path / "lambda.tf", encoding="utf-8") as f:
        content = f.read()
    section = _get_log_group_section(content, "dlq_reprocessor")
    assert "retention_in_days = 7" in section


def test_drift_recovery_log_group_has_7_day_retention(runners_src_path):
    """Verify drift_recovery log group has 7-day retention."""
    with open(runners_src_path / "lambda.tf", encoding="utf-8") as f:
        content = f.read()
    section = _get_log_group_section(content, "drift_recovery")
    assert "retention_in_days = 7" in section


def test_runners_handler_log_group_has_7_day_retention(runners_src_path):
    """Verify runners_handler log group has 7-day retention."""
    with open(runners_src_path / "lambda.tf", encoding="utf-8") as f:
        content = f.read()
    section = _get_log_group_section(content, "runners_handler")
    assert "retention_in_days = 7" in section


def test_runner_starter_log_group_has_7_day_retention(runners_src_path):
    """Verify runner_starter log group has 7-day retention."""
    with open(runners_src_path / "lambda.tf", encoding="utf-8") as f:
        content = f.read()
    section = _get_log_group_section(content, "runner_starter")
    assert "retention_in_days = 7" in section


def test_runner_terminator_log_group_has_7_day_retention(runners_src_path):
    """Verify runner_terminator log group has 7-day retention."""
    with open(runners_src_path / "lambda.tf", encoding="utf-8") as f:
        content = f.read()
    section = _get_log_group_section(content, "runner_terminator")
    assert "retention_in_days = 7" in section


# =============================================================================
# Log Subscription Filter Tests
# =============================================================================


def test_log_subscriptions_file_exists(runners_src_path):
    """Verify log_subscriptions.tf file exists."""
    log_subscriptions_file = runners_src_path / "log_subscriptions.tf"
    assert log_subscriptions_file.exists()


def test_log_subscriptions_references_firehose_from_api(runners_src_path):
    """Verify subscription filters reference Firehose from api remote state."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    assert "data.terraform_remote_state.api.outputs.firehose_cloudwatch_logs_arn" in content


def test_log_subscriptions_references_role_from_api(runners_src_path):
    """Verify subscription filters reference IAM role from api remote state."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    assert "data.terraform_remote_state.api.outputs.cloudwatch_logs_firehose_role_arn" in content


def test_runners_handler_subscription_filter_exists(runners_src_path):
    """Verify runners_handler subscription filter exists."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "runners_handler"' in content


def test_circuit_breaker_recovery_subscription_filter_exists(runners_src_path):
    """Verify circuit_breaker_recovery subscription filter exists."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "circuit_breaker_recovery"' in content


def test_circuit_breaker_remediation_subscription_filter_exists(runners_src_path):
    """Verify circuit_breaker_remediation subscription filter exists."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    resource = 'resource "aws_cloudwatch_log_subscription_filter"'
    assert f'{resource} "circuit_breaker_remediation"' in content


def test_dlq_reprocessor_subscription_filter_exists(runners_src_path):
    """Verify dlq_reprocessor subscription filter exists."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "dlq_reprocessor"' in content


def test_circuit_breaker_reset_subscription_filter_exists(runners_src_path):
    """Verify circuit_breaker_reset subscription filter exists."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "circuit_breaker_reset"' in content


def test_drift_recovery_subscription_filter_exists(runners_src_path):
    """Verify drift_recovery subscription filter exists."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "drift_recovery"' in content


def test_runner_starter_subscription_filter_exists(runners_src_path):
    """Verify runner_starter subscription filter exists."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "runner_starter"' in content


def test_runner_terminator_subscription_filter_exists(runners_src_path):
    """Verify runner_terminator subscription filter exists."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "runner_terminator"' in content


def test_ignored_events_archiver_subscription_filter_exists(runners_src_path):
    """Verify ignored_events_archiver subscription filter exists."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "ignored_events_archiver"' in content


def test_spot_interruption_handler_subscription_filter_exists(runners_src_path):
    """Verify spot_interruption_handler subscription filter exists."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    resource = 'resource "aws_cloudwatch_log_subscription_filter"'
    assert f'{resource} "spot_interruption_handler"' in content


def test_stale_runner_cleanup_subscription_filter_exists(runners_src_path):
    """Verify stale_runner_cleanup subscription filter exists."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_subscription_filter" "stale_runner_cleanup"' in content


def test_subscription_filters_use_conditional_creation(runners_src_path):
    """Verify subscription filters use count for conditional creation."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    assert "count           = local.create_subscriptions ? 1 : 0" in content


def test_subscription_filters_use_empty_filter_pattern(runners_src_path):
    """Verify subscription filters use empty filter pattern to capture all logs."""
    with open(runners_src_path / "log_subscriptions.tf", encoding="utf-8") as f:
        content = f.read()
    assert 'filter_pattern  = ""' in content
