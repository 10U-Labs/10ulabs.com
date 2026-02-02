"""Terraform unit tests for eventbridge.tf.

These tests verify the structure and configuration of EventBridge resources
defined in the Terraform configuration without making AWS calls.
"""

import re


class TestEventBridgeRuleResources:
    """Test EventBridge rule resources exist."""

    def test_config_compliance_change_rule_exists(self, eventbridge_tf_content):
        """Verify config compliance change rule is defined."""
        pattern = r'resource\s+"aws_cloudwatch_event_rule"\s+"config_compliance_change"'
        assert re.search(pattern, eventbridge_tf_content)

    def test_event_target_exists(self, eventbridge_tf_content):
        """Verify event target is defined."""
        pattern = r'resource\s+"aws_cloudwatch_event_target"\s+"lambda"'
        assert re.search(pattern, eventbridge_tf_content)


class TestEventBridgeRuleConfiguration:
    """Test EventBridge rule configuration."""

    def test_rule_listens_to_aws_config_source(self, eventbridge_tf_content):
        """Verify rule listens to aws.config source."""
        assert '"aws.config"' in eventbridge_tf_content

    def test_rule_listens_to_compliance_change_detail_type(self, eventbridge_tf_content):
        """Verify rule listens to Config Rules Compliance Change detail type."""
        assert '"Config Rules Compliance Change"' in eventbridge_tf_content

    def test_rule_filters_for_non_compliant(self, eventbridge_tf_content):
        """Verify rule filters for NON_COMPLIANT compliance type."""
        assert '"NON_COMPLIANT"' in eventbridge_tf_content


class TestEventBridgeTargetConfiguration:
    """Test EventBridge target configuration."""

    def test_target_references_lambda(self, eventbridge_tf_content):
        """Verify target references Lambda function."""
        pattern = r'arn\s*=\s*aws_lambda_function\.handler\.arn'
        assert re.search(pattern, eventbridge_tf_content)

    def test_target_has_input_transformer(self, eventbridge_tf_content):
        """Verify target has input transformer."""
        pattern = r'input_transformer\s*\{'
        assert re.search(pattern, eventbridge_tf_content)


class TestInputTransformerConfiguration:
    """Test input transformer configuration."""

    def test_input_paths_has_config_rule_name(self, eventbridge_tf_content):
        """Verify input paths extracts configRuleName."""
        pattern = r'configRuleName\s*=\s*"\$\.detail\.configRuleName"'
        assert re.search(pattern, eventbridge_tf_content)

    def test_input_paths_has_resource_type(self, eventbridge_tf_content):
        """Verify input paths extracts resourceType."""
        pattern = r'resourceType\s*=\s*"\$\.detail\.resourceType"'
        assert re.search(pattern, eventbridge_tf_content)

    def test_input_paths_has_resource_id(self, eventbridge_tf_content):
        """Verify input paths extracts resourceId."""
        pattern = r'resourceId\s*=\s*"\$\.detail\.resourceId"'
        assert re.search(pattern, eventbridge_tf_content)

    def test_input_paths_has_aws_region(self, eventbridge_tf_content):
        """Verify input paths extracts awsRegion."""
        pattern = r'awsRegion\s*=\s*"\$\.detail\.awsRegion"'
        assert re.search(pattern, eventbridge_tf_content)

    def test_input_template_has_source(self, eventbridge_tf_content):
        """Verify input template has drift-recovery-trigger source."""
        assert '"drift-recovery-trigger"' in eventbridge_tf_content
