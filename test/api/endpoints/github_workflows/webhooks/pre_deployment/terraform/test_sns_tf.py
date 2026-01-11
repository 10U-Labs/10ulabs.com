"""Terraform unit tests for sns.tf.

These tests verify SNS topics and subscriptions are correctly configured.
"""

import re


class TestSNSTopicsExist:
    """Test that expected SNS topics are defined."""

    def test_circuit_breaker_alerts_topic_exists(self, sns_tf_content):
        """Verify circuit_breaker_alerts SNS topic is defined."""
        pattern = r'resource\s+"aws_sns_topic"\s+"circuit_breaker_alerts"'
        assert re.search(pattern, sns_tf_content), (
            "SNS topic 'circuit_breaker_alerts' not found in sns.tf"
        )

    def test_topic_count_is_at_least_one(self, sns_tf_content):
        """Verify at least one SNS topic is defined."""
        topic_pattern = r'resource\s+"aws_sns_topic"\s+"\w+"'
        topic_count = len(re.findall(topic_pattern, sns_tf_content))
        assert topic_count >= 1, "Expected at least one SNS topic"


class TestSNSTopicConfiguration:
    """Test SNS topic configurations."""

    def test_topic_has_name(self, sns_tf_content):
        """Verify SNS topic has name defined."""
        pattern = r'name\s*=\s*"\$\{local\.resource_prefix\}'
        assert re.search(pattern, sns_tf_content), (
            "SNS topic name should use local.resource_prefix"
        )

    def test_topic_name_uses_resource_prefix(self, sns_tf_content):
        """Verify topic name uses local.resource_prefix for consistency."""
        assert 'local.resource_prefix' in sns_tf_content, (
            "Topic name should reference local.resource_prefix"
        )


class TestSNSSubscriptions:
    """Test SNS subscription configurations."""

    def test_email_subscription_exists(self, sns_tf_content):
        """Verify email subscription is defined."""
        pattern = r'resource\s+"aws_sns_topic_subscription"\s+"circuit_breaker_email"'
        assert re.search(pattern, sns_tf_content), (
            "Email subscription 'circuit_breaker_email' not found in sns.tf"
        )

    def test_email_subscription_uses_email_protocol(self, sns_tf_content):
        """Verify email subscription uses email protocol."""
        assert 'protocol  = "email"' in sns_tf_content, (
            "Email subscription should use email protocol"
        )

    def test_email_subscription_references_topic(self, sns_tf_content):
        """Verify email subscription references the alerts topic."""
        pattern = r'topic_arn\s*=\s*aws_sns_topic\.circuit_breaker_alerts\.arn'
        assert re.search(pattern, sns_tf_content), (
            "Email subscription should reference circuit_breaker_alerts topic"
        )

    def test_email_endpoint_uses_local_variable(self, sns_tf_content):
        """Verify email endpoint uses local variable for configurability."""
        pattern = r'endpoint\s*=\s*local\.'
        assert re.search(pattern, sns_tf_content), (
            "Email endpoint should use local variable"
        )


class TestSNSTags:
    """Test SNS resource tagging."""

    def test_topic_has_tags(self, sns_tf_content):
        """Verify SNS topic has tags defined."""
        pattern = r'tags\s*=\s*merge\(local\.common_tags'
        assert re.search(pattern, sns_tf_content), (
            "SNS topic should have tags using local.common_tags"
        )

    def test_tags_use_common_tags(self, sns_tf_content):
        """Verify tags reference local.common_tags for consistency."""
        assert 'local.common_tags' in sns_tf_content, (
            "Tags should reference local.common_tags"
        )
