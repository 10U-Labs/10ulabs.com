"""Post-deployment integration tests: Bedrock Guardrails.

Verifies the Bedrock Guardrail is deployed and configured correctly.

Five-layer testing model:
- Layer 3: Existence - Does the guardrail exist?
- Layer 4: Configuration - Are content/PII/topic policies configured?
"""

import pytest
from botocore.exceptions import ClientError


class TestGuardrailExistence:
    """Layer 3: Verify the Bedrock guardrail exists."""

    def test_01_guardrail_exists(self, bedrock_client, guardrail_name):
        """Verify the Bedrock guardrail exists."""
        try:
            response = bedrock_client.list_guardrails(maxResults=100)
            guardrails = response.get("guardrails", [])
            names = [g["name"] for g in guardrails]
            assert guardrail_name in names, (
                f"Guardrail '{guardrail_name}' not found. "
                f"Available guardrails: {names}. "
                "Run terraform apply to create it."
            )
        except ClientError as err:
            pytest.fail(f"Failed to list guardrails: {err}")


class TestGuardrailConfiguration:
    """Layer 4: Verify the guardrail is configured correctly."""

    @pytest.fixture
    def guardrail_id(self, bedrock_client, guardrail_name):
        """Get the guardrail ID by name."""
        response = bedrock_client.list_guardrails(maxResults=100)
        for g in response.get("guardrails", []):
            if g["name"] == guardrail_name:
                return g["id"]
        pytest.skip(f"Guardrail '{guardrail_name}' not found")

    def test_01_guardrail_has_content_policy(
        self, bedrock_client, guardrail_id, guardrail_name
    ):
        """Verify the guardrail has content policy configured."""
        try:
            response = bedrock_client.get_guardrail(
                guardrailIdentifier=guardrail_id
            )
            content_policy = response.get("contentPolicy")
            assert content_policy is not None, (
                f"Guardrail '{guardrail_name}' should have content policy configured."
            )
        except ClientError as err:
            pytest.fail(f"Failed to get guardrail: {err}")

    def test_02_guardrail_has_content_filters(
        self, bedrock_client, guardrail_id, guardrail_name
    ):
        """Verify the guardrail has content filters configured."""
        try:
            response = bedrock_client.get_guardrail(
                guardrailIdentifier=guardrail_id
            )
            content_policy = response.get("contentPolicy", {})
            filters = content_policy.get("filters", [])
            assert len(filters) > 0, (
                f"Guardrail '{guardrail_name}' should have content filters configured."
            )
        except ClientError as err:
            pytest.fail(f"Failed to get guardrail: {err}")

    def test_03_guardrail_has_sensitive_info_policy(
        self, bedrock_client, guardrail_id, guardrail_name
    ):
        """Verify the guardrail has sensitive information policy configured."""
        try:
            response = bedrock_client.get_guardrail(
                guardrailIdentifier=guardrail_id
            )
            sensitive_policy = response.get("sensitiveInformationPolicy")
            assert sensitive_policy is not None, (
                f"Guardrail '{guardrail_name}' should have sensitive info policy configured."
            )
        except ClientError as err:
            pytest.fail(f"Failed to get guardrail: {err}")

    def test_04_guardrail_has_topic_policy(
        self, bedrock_client, guardrail_id, guardrail_name
    ):
        """Verify the guardrail has topic policy configured."""
        try:
            response = bedrock_client.get_guardrail(
                guardrailIdentifier=guardrail_id
            )
            topic_policy = response.get("topicPolicy")
            assert topic_policy is not None, (
                f"Guardrail '{guardrail_name}' should have topic policy configured."
            )
        except ClientError as err:
            pytest.fail(f"Failed to get guardrail: {err}")

    def test_05_guardrail_has_word_policy(
        self, bedrock_client, guardrail_id, guardrail_name
    ):
        """Verify the guardrail has word policy configured."""
        try:
            response = bedrock_client.get_guardrail(
                guardrailIdentifier=guardrail_id
            )
            word_policy = response.get("wordPolicy")
            assert word_policy is not None, (
                f"Guardrail '{guardrail_name}' should have word policy configured."
            )
        except ClientError as err:
            pytest.fail(f"Failed to get guardrail: {err}")

    def test_06_guardrail_has_version(
        self, bedrock_client, guardrail_id, guardrail_name
    ):
        """Verify the guardrail has at least one version."""
        try:
            response = bedrock_client.list_guardrails(
                guardrailIdentifier=guardrail_id
            )
            guardrails = response.get("guardrails", [])
            versions = [g.get("version") for g in guardrails if g.get("version")]
            assert len(versions) > 0, (
                f"Guardrail '{guardrail_name}' should have at least one version."
            )
        except ClientError as err:
            pytest.fail(f"Failed to list guardrail versions: {err}")
