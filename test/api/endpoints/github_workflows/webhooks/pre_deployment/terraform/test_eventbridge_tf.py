"""Terraform unit tests for eventbridge.tf.

These tests verify EventBridge rules and targets are correctly configured.
"""

import re

import pytest

# Expected EventBridge rules (rule_name -> target_name)
# Most rules have matching target names, but some don't
EVENTBRIDGE_RULES = [
    "circuit_breaker_remediation",
    "dlq_reprocessor",
    "circuit_breaker_recovery",
    "ecs_task_stopped",
    "ec2_spot_interruption",
    "stale_runner_cleanup_schedule",
]

# Map rule names to target names (when they differ)
RULE_TO_TARGET_NAME = {
    "stale_runner_cleanup_schedule": "stale_runner_cleanup",
}

# Rules that use schedule expressions
SCHEDULED_RULES = [
    "dlq_reprocessor",
    "circuit_breaker_recovery",
    "stale_runner_cleanup_schedule",
]

# Rules that use event patterns
EVENT_PATTERN_RULES = [
    "circuit_breaker_remediation",
    "ecs_task_stopped",
    "ec2_spot_interruption",
]


class TestEventBridgeRulesExist:
    """Test that all expected EventBridge rules are defined."""

    @pytest.mark.parametrize("rule_name", EVENTBRIDGE_RULES)
    def test_eventbridge_rule_exists(self, eventbridge_tf_content, rule_name):
        """Verify EventBridge rule resource is defined."""
        pattern = rf'resource\s+"aws_cloudwatch_event_rule"\s+"{rule_name}"'
        assert re.search(pattern, eventbridge_tf_content), (
            f"EventBridge rule '{rule_name}' not found in eventbridge.tf"
        )


class TestEventBridgeTargetsExist:
    """Test that EventBridge targets are defined for each rule."""

    @pytest.mark.parametrize("rule_name", EVENTBRIDGE_RULES)
    def test_eventbridge_target_exists(self, eventbridge_tf_content, rule_name):
        """Verify EventBridge target resource is defined."""
        # Get the target name (may differ from rule name)
        target_name = RULE_TO_TARGET_NAME.get(rule_name, rule_name)
        pattern = rf'resource\s+"aws_cloudwatch_event_target"\s+"{target_name}"'
        assert re.search(pattern, eventbridge_tf_content), (
            f"EventBridge target '{target_name}' for rule '{rule_name}' not found in eventbridge.tf"
        )


class TestEventBridgeLambdaPermissions:
    """Test that Lambda permissions are defined for EventBridge invocations."""

    def test_lambda_permissions_exist(self, eventbridge_tf_content):
        """Verify Lambda permission resources exist for EventBridge."""
        permission_count = len(re.findall(r'resource\s+"aws_lambda_permission"', eventbridge_tf_content))
        rule_count = len(EVENTBRIDGE_RULES)
        assert permission_count >= rule_count, (
            f"Expected at least {rule_count} Lambda permissions, found {permission_count}"
        )

    def test_permissions_allow_invoke(self, eventbridge_tf_content):
        """Verify permissions allow lambda:InvokeFunction action."""
        assert '"lambda:InvokeFunction"' in eventbridge_tf_content, (
            "Lambda permissions should allow lambda:InvokeFunction"
        )

    def test_permissions_use_events_principal(self, eventbridge_tf_content):
        """Verify permissions use events.amazonaws.com principal."""
        assert '"events.amazonaws.com"' in eventbridge_tf_content, (
            "Lambda permissions should use events.amazonaws.com principal"
        )


class TestScheduledRules:
    """Test scheduled EventBridge rule configurations."""

    @pytest.mark.parametrize("rule_name", SCHEDULED_RULES)
    def test_scheduled_rule_has_expression(self, eventbridge_tf_content, rule_name):
        """Verify scheduled rules have schedule_expression defined."""
        # Find the rule resource block
        rule_pattern = rf'resource\s+"aws_cloudwatch_event_rule"\s+"{rule_name}"'
        match = re.search(rule_pattern, eventbridge_tf_content)
        assert match, f"Rule '{rule_name}' not found"

        # Look for schedule_expression in the block
        start_pos = match.end()
        block_end = eventbridge_tf_content.find('\nresource', start_pos)
        if block_end == -1:
            block_end = len(eventbridge_tf_content)
        block = eventbridge_tf_content[start_pos:block_end]

        assert 'schedule_expression' in block, (
            f"Schedule expression not found for rule '{rule_name}'"
        )

    def test_dlq_reprocessor_runs_periodically(self, eventbridge_tf_content):
        """Verify DLQ reprocessor runs on a schedule."""
        assert 'rate(15 minutes)' in eventbridge_tf_content, (
            "DLQ reprocessor should run every 15 minutes"
        )

    def test_circuit_breaker_recovery_runs_periodically(self, eventbridge_tf_content):
        """Verify circuit breaker recovery runs on a schedule."""
        assert 'rate(5 minutes)' in eventbridge_tf_content, (
            "Circuit breaker recovery should run periodically"
        )


class TestEventPatternRules:
    """Test event pattern EventBridge rule configurations."""

    @pytest.mark.parametrize("rule_name", EVENT_PATTERN_RULES)
    def test_event_pattern_rule_has_pattern(self, eventbridge_tf_content, rule_name):
        """Verify event pattern rules have event_pattern defined."""
        rule_pattern = rf'resource\s+"aws_cloudwatch_event_rule"\s+"{rule_name}"'
        match = re.search(rule_pattern, eventbridge_tf_content)
        assert match, f"Rule '{rule_name}' not found"

        start_pos = match.end()
        block_end = eventbridge_tf_content.find('\nresource', start_pos)
        if block_end == -1:
            block_end = len(eventbridge_tf_content)
        block = eventbridge_tf_content[start_pos:block_end]

        assert 'event_pattern' in block, (
            f"Event pattern not found for rule '{rule_name}'"
        )

    def test_circuit_breaker_remediation_listens_to_cloudwatch(self, eventbridge_tf_content):
        """Verify circuit breaker remediation listens to CloudWatch alarm changes."""
        assert '"aws.cloudwatch"' in eventbridge_tf_content, (
            "Circuit breaker remediation should listen to aws.cloudwatch events"
        )
        assert '"CloudWatch Alarm State Change"' in eventbridge_tf_content, (
            "Circuit breaker remediation should listen to alarm state changes"
        )

    def test_ecs_task_stopped_listens_to_ecs(self, eventbridge_tf_content):
        """Verify ECS task stopped rule listens to ECS events."""
        assert '"aws.ecs"' in eventbridge_tf_content, (
            "ECS task stopped rule should listen to aws.ecs events"
        )
        assert '"ECS Task State Change"' in eventbridge_tf_content, (
            "ECS task stopped rule should listen to ECS Task State Change events"
        )

    def test_ec2_spot_interruption_listens_to_ec2(self, eventbridge_tf_content):
        """Verify EC2 spot interruption rule listens to EC2 events."""
        assert '"aws.ec2"' in eventbridge_tf_content, (
            "EC2 spot interruption rule should listen to aws.ec2 events"
        )
        assert '"EC2 Spot Instance Interruption Warning"' in eventbridge_tf_content, (
            "EC2 spot interruption rule should listen to spot interruption warnings"
        )


class TestEventBridgeNamingConventions:
    """Test EventBridge naming conventions."""

    def test_rule_names_use_resource_prefix(self, eventbridge_tf_content):
        """Verify rule names use local.resource_prefix."""
        pattern = r'name\s*=\s*"\$\{local\.resource_prefix\}'
        prefix_count = len(re.findall(pattern, eventbridge_tf_content))
        rule_count = len(re.findall(r'resource\s+"aws_cloudwatch_event_rule"', eventbridge_tf_content))
        assert prefix_count >= rule_count, (
            f"Not all rule names use resource_prefix: "
            f"found {prefix_count} for {rule_count} rules"
        )


class TestEventBridgeTags:
    """Test EventBridge resource tagging."""

    def test_rules_have_tags(self, eventbridge_tf_content):
        """Verify rules have tags defined."""
        rule_count = len(re.findall(r'resource\s+"aws_cloudwatch_event_rule"', eventbridge_tf_content))
        tags_count = len(re.findall(r'tags\s*=\s*merge\(local\.common_tags', eventbridge_tf_content))
        assert tags_count >= rule_count, (
            f"Not all rules have tags: found {tags_count} for {rule_count} rules"
        )


class TestEventBridgeTargetConfiguration:
    """Test EventBridge target configurations."""

    def test_targets_reference_lambda_functions(self, eventbridge_tf_content):
        """Verify targets reference Lambda function ARNs."""
        target_count = len(re.findall(r'resource\s+"aws_cloudwatch_event_target"', eventbridge_tf_content))
        lambda_arn_count = len(re.findall(r'arn\s*=\s*aws_lambda_function\.\w+\.arn', eventbridge_tf_content))
        assert lambda_arn_count >= target_count, (
            f"Not all targets reference Lambda ARNs: "
            f"found {lambda_arn_count} for {target_count} targets"
        )

    def test_targets_have_target_ids(self, eventbridge_tf_content):
        """Verify targets have target_id defined."""
        target_count = len(re.findall(r'resource\s+"aws_cloudwatch_event_target"', eventbridge_tf_content))
        target_id_count = len(re.findall(r'target_id\s*=', eventbridge_tf_content))
        assert target_id_count >= target_count, (
            f"Not all targets have target_id: "
            f"found {target_id_count} for {target_count} targets"
        )
