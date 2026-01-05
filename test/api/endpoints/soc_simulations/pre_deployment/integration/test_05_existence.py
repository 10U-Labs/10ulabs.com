"""Layer 5: Existence tests for soc_simulations endpoint.

Tests that prerequisite resources exist. Assumes authorization passed.
These test resources created by OTHER workflows that this endpoint depends on.
"""
import pytest

from test_fixtures.integration import (
    Layer4TerraformStateExistenceTests,
    Layer5APIBackendPrerequisiteTests,
)

pytestmark = pytest.mark.layer(5)

pytest_plugins = ['test_fixtures.aws']


class TestTerraformStateExistence(Layer4TerraformStateExistenceTests):
    """Tests that Terraform state bucket exists."""


class TestAPIBackendPrerequisites(Layer5APIBackendPrerequisiteTests):
    """Tests that API Gateway backend prerequisites exist."""


def test_api_gateway_exists(api_gateway_info):
    """Verify API Gateway exists."""
    api_exists = api_gateway_info.get("exists") is True
    assert api_exists, (
        f"API Gateway {api_gateway_info.get('id')} does not exist. "
        "Deploy api_common_routing first."
    )
