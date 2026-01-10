"""Terraform unit tests for cloudwatch.tf.

These tests verify CloudWatch alarms are correctly configured.
"""

import re

import pytest

# Expected CloudWatch alarms
CLOUDWATCH_ALARMS = [
    "circuit_breaker_open",
    "circuit_breaker_high_failures",
    "webhook_handler_errors",
    "runners_dlq_messages",
]


class TestCloudWatchAlarmsExist:
    """Test that all expected CloudWatch alarms are defined."""

    @pytest.mark.parametrize("alarm_name", CLOUDWATCH_ALARMS)
    def test_cloudwatch_alarm_exists(self, cloudwatch_tf_content, alarm_name):
        """Verify CloudWatch alarm resource is defined."""
        pattern = rf'resource\s+"aws_cloudwatch_metric_alarm"\s+"{alarm_name}"'
        assert re.search(pattern, cloudwatch_tf_content), (
            f"CloudWatch alarm '{alarm_name}' not found in cloudwatch.tf"
        )


class TestCloudWatchAlarmConfiguration:
    """Test CloudWatch alarm configurations."""

    def test_alarms_have_comparison_operator(self, cloudwatch_tf_content):
        """Verify alarms have comparison_operator defined."""
        alarm_count = len(re.findall(r'resource\s+"aws_cloudwatch_metric_alarm"', cloudwatch_tf_content))
        operator_count = len(re.findall(r'comparison_operator\s*=', cloudwatch_tf_content))
        assert operator_count >= alarm_count, (
            f"Not all alarms have comparison_operator: "
            f"found {operator_count} for {alarm_count} alarms"
        )

    def test_alarms_have_evaluation_periods(self, cloudwatch_tf_content):
        """Verify alarms have evaluation_periods defined."""
        alarm_count = len(re.findall(r'resource\s+"aws_cloudwatch_metric_alarm"', cloudwatch_tf_content))
        periods_count = len(re.findall(r'evaluation_periods\s*=', cloudwatch_tf_content))
        assert periods_count >= alarm_count, (
            f"Not all alarms have evaluation_periods: "
            f"found {periods_count} for {alarm_count} alarms"
        )

    def test_alarms_have_treat_missing_data(self, cloudwatch_tf_content):
        """Verify alarms have treat_missing_data set to notBreaching."""
        alarm_count = len(re.findall(r'resource\s+"aws_cloudwatch_metric_alarm"', cloudwatch_tf_content))
        not_breaching_count = len(re.findall(r'treat_missing_data\s*=\s*"notBreaching"', cloudwatch_tf_content))
        assert not_breaching_count >= alarm_count, (
            f"Not all alarms use notBreaching for missing data: "
            f"found {not_breaching_count} for {alarm_count} alarms"
        )


class TestCloudWatchAlarmActions:
    """Test CloudWatch alarm action configurations."""

    def test_alarms_have_alarm_actions(self, cloudwatch_tf_content):
        """Verify alarms have alarm_actions configured."""
        alarm_count = len(re.findall(r'resource\s+"aws_cloudwatch_metric_alarm"', cloudwatch_tf_content))
        actions_count = len(re.findall(r'alarm_actions\s*=', cloudwatch_tf_content))
        assert actions_count >= alarm_count, (
            f"Not all alarms have alarm_actions: "
            f"found {actions_count} for {alarm_count} alarms"
        )

    def test_alarms_reference_sns_topic(self, cloudwatch_tf_content):
        """Verify alarms send notifications to SNS topic."""
        pattern = r'aws_sns_topic\.circuit_breaker_alerts\.arn'
        assert re.search(pattern, cloudwatch_tf_content), (
            "Alarms should reference circuit_breaker_alerts SNS topic"
        )


class TestCloudWatchAlarmDescriptions:
    """Test CloudWatch alarm descriptions."""

    def test_alarms_have_descriptions(self, cloudwatch_tf_content):
        """Verify alarms have alarm_description defined."""
        alarm_count = len(re.findall(r'resource\s+"aws_cloudwatch_metric_alarm"', cloudwatch_tf_content))
        desc_count = len(re.findall(r'alarm_description\s*=', cloudwatch_tf_content))
        assert desc_count >= alarm_count, (
            f"Not all alarms have alarm_description: "
            f"found {desc_count} for {alarm_count} alarms"
        )


class TestCloudWatchAlarmNamingConventions:
    """Test CloudWatch alarm naming conventions."""

    def test_alarm_names_use_resource_prefix(self, cloudwatch_tf_content):
        """Verify alarm names use local.resource_prefix."""
        pattern = r'alarm_name\s*=\s*"\$\{local\.resource_prefix\}'
        prefix_count = len(re.findall(pattern, cloudwatch_tf_content))
        alarm_count = len(re.findall(r'resource\s+"aws_cloudwatch_metric_alarm"', cloudwatch_tf_content))
        assert prefix_count >= alarm_count, (
            f"Not all alarm names use resource_prefix: "
            f"found {prefix_count} for {alarm_count} alarms"
        )


class TestCloudWatchAlarmTags:
    """Test CloudWatch alarm tagging."""

    def test_alarms_have_tags(self, cloudwatch_tf_content):
        """Verify alarms have tags defined."""
        alarm_count = len(re.findall(r'resource\s+"aws_cloudwatch_metric_alarm"', cloudwatch_tf_content))
        tags_count = len(re.findall(r'tags\s*=\s*merge\(local\.common_tags', cloudwatch_tf_content))
        assert tags_count >= alarm_count, (
            f"Not all alarms have tags: found {tags_count} for {alarm_count} alarms"
        )


class TestCircuitBreakerAlarms:
    """Test circuit breaker specific alarm configurations."""

    def test_circuit_breaker_open_alarm_configuration(self, cloudwatch_tf_content):
        """Verify circuit breaker open alarm has correct metric configuration."""
        assert '"CircuitBreakerState"' in cloudwatch_tf_content, (
            "CircuitBreakerState metric not found"
        )
        assert '"WebhookRouter"' in cloudwatch_tf_content, (
            "WebhookRouter namespace not found"
        )

    def test_webhook_handler_errors_uses_metric_query(self, cloudwatch_tf_content):
        """Verify webhook handler errors alarm uses metric queries for error rate."""
        pattern = r'metric_query\s*\{'
        query_count = len(re.findall(pattern, cloudwatch_tf_content))
        assert query_count >= 3, (
            f"Expected at least 3 metric queries for error rate calculation, "
            f"found {query_count}"
        )

    def test_error_rate_expression_defined(self, cloudwatch_tf_content):
        """Verify error rate expression is defined."""
        pattern = r'expression\s*=\s*"errors\s*/\s*invocations\s*\*\s*100"'
        assert re.search(pattern, cloudwatch_tf_content), (
            "Error rate expression not found in webhook_handler_errors alarm"
        )


class TestDLQAlarm:
    """Test DLQ monitoring alarm configuration."""

    def test_dlq_alarm_monitors_messages_visible(self, cloudwatch_tf_content):
        """Verify DLQ alarm monitors ApproximateNumberOfMessagesVisible."""
        assert '"ApproximateNumberOfMessagesVisible"' in cloudwatch_tf_content, (
            "DLQ alarm should monitor ApproximateNumberOfMessagesVisible metric"
        )

    def test_dlq_alarm_uses_sqs_namespace(self, cloudwatch_tf_content):
        """Verify DLQ alarm uses AWS/SQS namespace."""
        assert '"AWS/SQS"' in cloudwatch_tf_content, (
            "DLQ alarm should use AWS/SQS namespace"
        )
