"""Layer 2: Authentication tests for api_common_routing pre-deployment validation.

Verify AWS credentials are valid before testing authorization or state.
"""
import pytest
from test_fixtures.integration import Layer2EndpointAuthenticationTests



class TestAuthentication(Layer2EndpointAuthenticationTests):
    """Inherit standard authentication tests."""


def test_caller_identity_is_role(caller_identity):
    """Verify we are running as an IAM role (not user)."""
    arn = caller_identity.get("Arn", "")
    assert ":assumed-role/" in arn or ":role/" in arn, (
        f"Expected to be running as IAM role, but running as: {arn}. "
        "GitHub Actions should assume the GitHub Actions OIDC role."
    )
