"""Terraform unit tests for eventbridge.tf.

These tests verify EventBridge rules and targets are correctly configured.
"""

import re

import pytest

# Expected EventBridge rules (rule_name -> target_name)
# Most rules have matching target names, but some don't
EVENTBRIDGE_RULES = [
    "circuit_open_remediations",
    "dlq_reprocessor",
    "circuit_open_recoveries",
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
    "circuit_open_recoveries",
    "stale_runner_cleanup_schedule",
]

# Rules that use event patterns
EVENT_PATTERN_RULES = [
    "circuit_open_remediations",
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

    def test_rule_count_matches_expected(self, eventbridge_tf_content):
        """Verify the number of EventBridge rules matches expected count."""
        rule_pattern = r'resource\s+"aws_cloudwatch_event_rule"\s+"\w+"'
        actual_count = len(re.findall(rule_pattern, eventbridge_tf_content))
        assert actual_count >= len(EVENTBRIDGE_RULES), (
            f"Expected at least {len(EVENTBRIDGE_RULES)} rules, found {actual_count}"
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

    def test_target_count_matches_rule_count(self, eventbridge_tf_content):
        """Verify target count matches or exceeds rule count."""
        rule_pattern = r'resource\s+"aws_cloudwatch_event_rule"'
        target_pattern = r'resource\s+"aws_cloudwatch_event_target"'
        rule_count = len(re.findall(rule_pattern, eventbridge_tf_content))
        target_count = len(re.findall(target_pattern, eventbridge_tf_content))
        assert target_count >= rule_count, (
            f"Expected at least {rule_count} targets for {rule_count} rules"
        )


class TestEventBridgeLambdaPermissions:
    """Test that Lambda permissions are defined for EventBridge invocations."""

    def test_lambda_permissions_exist(self, eventbridge_tf_content):
        """Verify Lambda permission resources exist for EventBridge."""
        permission_pattern = r'resource\s+"aws_lambda_permission"'
        permission_count = len(re.findall(permission_pattern, eventbridge_tf_content))
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

        # Look for schedule_expression in the block
        if match:
            start_pos = match.end()
            block_end = eventbridge_tf_content.find('\nresource', start_pos)
            if block_end == -1:
                block_end = len(eventbridge_tf_content)
            block = eventbridge_tf_content[start_pos:block_end]
        else:
            block = ""

        assert match and 'schedule_expression' in block

    def test_dlq_reprocessor_runs_periodically(self, eventbridge_tf_content):
        """Verify DLQ reprocessor runs on a schedule."""
        assert 'rate(15 minutes)' in eventbridge_tf_content, (
            "DLQ reprocessor should run every 15 minutes"
        )

    def test_circuit_open_recoveries_runs_periodically(self, eventbridge_tf_content):
        """Verify circuit open recovery runs on a schedule."""
        assert 'rate(5 minutes)' in eventbridge_tf_content, (
            "Circuit open recovery should run periodically"
        )


class TestEventPatternRules:
    """Test event pattern EventBridge rule configurations."""

    @pytest.mark.parametrize("rule_name", EVENT_PATTERN_RULES)
    def test_event_pattern_rule_has_pattern(self, eventbridge_tf_content, rule_name):
        """Verify event pattern rules have event_pattern defined."""
        rule_pattern = rf'resource\s+"aws_cloudwatch_event_rule"\s+"{rule_name}"'
        match = re.search(rule_pattern, eventbridge_tf_content)

        if match:
            start_pos = match.end()
            block_end = eventbridge_tf_content.find('\nresource', start_pos)
            if block_end == -1:
                block_end = len(eventbridge_tf_content)
            block = eventbridge_tf_content[start_pos:block_end]
        else:
            block = ""

        assert match and 'event_pattern' in block

    def test_circuit_open_remediations_listens_to_cloudwatch(self, eventbridge_tf_content):
        """Verify circuit open remediation listens to CloudWatch alarm changes."""
        has_cw = '"aws.cloudwatch"' in eventbridge_tf_content
        has_alarm = '"CloudWatch Alarm State Change"' in eventbridge_tf_content
        assert has_cw and has_alarm

    def test_ecs_task_stopped_listens_to_ecs(self, eventbridge_tf_content):
        """Verify ECS task stopped rule listens to ECS events."""
        has_ecs = '"aws.ecs"' in eventbridge_tf_content
        has_task = '"ECS Task State Change"' in eventbridge_tf_content
        assert has_ecs and has_task

    def test_ec2_spot_interruption_listens_to_ec2(self, eventbridge_tf_content):
        """Verify EC2 spot interruption rule listens to EC2 events."""
        has_ec2 = '"aws.ec2"' in eventbridge_tf_content
        has_spot = '"EC2 Spot Instance Interruption Warning"' in eventbridge_tf_content
        assert has_ec2 and has_spot


class TestEventBridgeNamingConventions:
    """Test EventBridge naming conventions."""

    def test_rule_names_use_resource_prefix(self, eventbridge_tf_content):
        """Verify rule names use local.resource_prefix."""
        pattern = r'name\s*=\s*"\$\{local\.resource_prefix\}'
        prefix_count = len(re.findall(pattern, eventbridge_tf_content))
        rule_pattern = r'resource\s+"aws_cloudwatch_event_rule"'
        rule_count = len(re.findall(rule_pattern, eventbridge_tf_content))
        assert prefix_count >= rule_count, (
            f"Not all rule names use resource_prefix: "
            f"found {prefix_count} for {rule_count} rules"
        )

    def test_no_hardcoded_rule_names(self, eventbridge_tf_content):
        """Verify rule names are not hardcoded."""
        hardcoded = r'aws_cloudwatch_event_rule"[^}]*name\s*=\s*"[^$\{]'
        hardcoded_count = len(re.findall(hardcoded, eventbridge_tf_content, re.DOTALL))
        assert hardcoded_count == 0, "Rule names should use resource_prefix"


class TestEventBridgeTags:
    """Test EventBridge resource tagging."""

    def test_rules_have_tags(self, eventbridge_tf_content):
        """Verify rules have tags defined."""
        rule_pattern = r'resource\s+"aws_cloudwatch_event_rule"'
        rule_count = len(re.findall(rule_pattern, eventbridge_tf_content))
        tags_pattern = r'tags\s*=\s*merge\(local\.common_tags'
        tags_count = len(re.findall(tags_pattern, eventbridge_tf_content))
        assert tags_count >= rule_count, (
            f"Not all rules have tags: found {tags_count} for {rule_count} rules"
        )

    def test_tags_use_common_tags(self, eventbridge_tf_content):
        """Verify tags reference local.common_tags for consistency."""
        assert 'local.common_tags' in eventbridge_tf_content, (
            "Tags should reference local.common_tags"
        )


class TestEventBridgeTargetConfiguration:
    """Test EventBridge target configurations."""

    def test_targets_reference_lambda_functions(self, eventbridge_tf_content):
        """Verify targets reference Lambda function ARNs."""
        target_pattern = r'resource\s+"aws_cloudwatch_event_target"'
        target_count = len(re.findall(target_pattern, eventbridge_tf_content))
        arn_pattern = r'arn\s*=\s*aws_lambda_function\.\w+\.arn'
        lambda_arn_count = len(re.findall(arn_pattern, eventbridge_tf_content))
        assert lambda_arn_count >= target_count, (
            f"Not all targets reference Lambda ARNs: "
            f"found {lambda_arn_count} for {target_count} targets"
        )

    def test_targets_have_target_ids(self, eventbridge_tf_content):
        """Verify targets have target_id defined."""
        target_pattern = r'resource\s+"aws_cloudwatch_event_target"'
        target_count = len(re.findall(target_pattern, eventbridge_tf_content))
        target_id_count = len(re.findall(r'target_id\s*=', eventbridge_tf_content))
        assert target_id_count >= target_count, (
            f"Not all targets have target_id: "
            f"found {target_id_count} for {target_count} targets"
        )
