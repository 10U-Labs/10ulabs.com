"""Terraform unit tests for sns.tf.

These tests verify the structure and configuration of SNS resources
defined in the Terraform configuration without making AWS calls.
"""

import re


class TestSNSTopicResources:
    """Test SNS topic resources exist."""

    def test_alerts_topic_exists(self, sns_tf_content):
        """Verify alerts SNS topic is defined."""
        pattern = r'resource\s+"aws_sns_topic"\s+"alerts"'
        assert re.search(pattern, sns_tf_content)

    def test_email_subscription_exists(self, sns_tf_content):
        """Verify email subscription is defined."""
        pattern = r'resource\s+"aws_sns_topic_subscription"\s+"alerts_email"'
        assert re.search(pattern, sns_tf_content)

    def test_topic_name_uses_resource_prefix(self, sns_tf_content):
        """Verify topic name uses resource prefix."""
        pattern = r'name\s*=\s*"\$\{local\.resource_prefix\}-drift-recovery-alerts"'
        assert re.search(pattern, sns_tf_content)


class TestSNSSubscriptionConfiguration:
    """Test SNS subscription configuration."""

    def test_subscription_protocol_is_email(self, sns_tf_content):
        """Verify subscription protocol is email."""
        pattern = r'protocol\s*=\s*"email"'
        assert re.search(pattern, sns_tf_content)

    def test_subscription_references_topic(self, sns_tf_content):
        """Verify subscription references the alerts topic."""
        pattern = r'topic_arn\s*=\s*aws_sns_topic\.alerts\.arn'
        assert re.search(pattern, sns_tf_content)

    def test_subscription_uses_local_email(self, sns_tf_content):
        """Verify subscription uses local.alert_email."""
        pattern = r'endpoint\s*=\s*local\.alert_email'
        assert re.search(pattern, sns_tf_content)
