"""Terraform unit tests for eventbridge.tf.

These tests verify the structure and configuration of EventBridge resources
defined in the Terraform configuration without making AWS calls.
"""

import re


class TestEventBridgeRuleResources:
    """Test EventBridge rule resources exist."""

    def test_scheduled_check_rule_exists(self, eventbridge_tf_content):
        """Verify scheduled check rule is defined."""
        pattern = r'resource\s+"aws_cloudwatch_event_rule"\s+"scheduled_check"'
        assert re.search(pattern, eventbridge_tf_content)

    def test_event_target_exists(self, eventbridge_tf_content):
        """Verify event target is defined."""
        pattern = r'resource\s+"aws_cloudwatch_event_target"\s+"lambda"'
        assert re.search(pattern, eventbridge_tf_content)

    def test_lambda_permission_exists(self, eventbridge_tf_content):
        """Verify Lambda permission for EventBridge is defined."""
        pattern = r'resource\s+"aws_lambda_permission"\s+"eventbridge"'
        assert re.search(pattern, eventbridge_tf_content)


class TestEventBridgeRuleConfiguration:
    """Test EventBridge rule configuration."""

    def test_rule_has_schedule_expression(self, eventbridge_tf_content):
        """Verify rule has schedule expression."""
        pattern = r'schedule_expression\s*='
        assert re.search(pattern, eventbridge_tf_content)

    def test_rule_uses_rate_schedule(self, eventbridge_tf_content):
        """Verify rule uses rate-based schedule."""
        pattern = r'rate\(1 hour\)'
        assert re.search(pattern, eventbridge_tf_content)


class TestEventBridgeTargetConfiguration:
    """Test EventBridge target configuration."""

    def test_target_references_lambda(self, eventbridge_tf_content):
        """Verify target references Lambda function."""
        pattern = r'arn\s*=\s*aws_lambda_function\.handler\.arn'
        assert re.search(pattern, eventbridge_tf_content)

    def test_target_has_invoke_lambda_id(self, eventbridge_tf_content):
        """Verify target has InvokeLambda target ID."""
        pattern = r'target_id\s*=\s*"InvokeLambda"'
        assert re.search(pattern, eventbridge_tf_content)


class TestLambdaPermissionConfiguration:
    """Test Lambda permission configuration for EventBridge."""

    def test_permission_allows_invoke(self, eventbridge_tf_content):
        """Verify permission allows lambda:InvokeFunction."""
        assert '"lambda:InvokeFunction"' in eventbridge_tf_content

    def test_permission_principal_is_events(self, eventbridge_tf_content):
        """Verify permission principal is events.amazonaws.com."""
        assert '"events.amazonaws.com"' in eventbridge_tf_content
