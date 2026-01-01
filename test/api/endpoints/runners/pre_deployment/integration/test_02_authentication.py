"""Layer 2: Authentication tests for runners endpoint pre-deployment validation.

Verify AWS credentials are valid before testing authorization or state.
"""
import os

import pytest
from test_fixtures.integration import Layer2EndpointAuthenticationTests

pytestmark = pytest.mark.layer(2)


class TestAuthentication(Layer2EndpointAuthenticationTests):
    """Inherit standard authentication tests."""


@pytest.mark.skipif(
    os.environ.get("GITHUB_ACTIONS") != "true",
    reason="Role identity check only applies in GitHub Actions"
)
def test_caller_identity_is_role(current_identity):
    """Verify we are running as an IAM role (not user)."""
    arn = current_identity.get("Arn", "")
    assert ":assumed-role/" in arn or ":role/" in arn, (
        f"Expected to be running as IAM role, but running as: {arn}. "
        "GitHub Actions should assume the GitHub Actions OIDC role."
    )
