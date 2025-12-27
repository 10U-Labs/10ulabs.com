"""Layer 4: Existence tests for contact endpoint pre-deployment.

Tests that prerequisite resources exist. Assumes authorization passed.
These tests verify resources from OTHER workflows that THIS workflow depends on.

Six-layer testing model:
- Layer 4: Existence - Prerequisite resources exist
"""

import pytest
from test_fixtures.integration import assert_api_gateway_exists


pytestmark = pytest.mark.layer(4)


class TestPrerequisiteExistence:
    """Layer 4: Verify prerequisite resources exist."""

    def test_api_gateway_rest_api_exists(self, api_gateway_info):
        """Verify API Gateway REST API exists."""
        assert_api_gateway_exists(api_gateway_info)

    def test_ses_sending_is_enabled(self, ses_client):
        """Verify SES sending is enabled in the region."""
        response = ses_client.get_account_sending_enabled()
        assert response.get("Enabled", False), (
            "SES sending is not enabled in this region. "
            "Enable SES sending or request production access from AWS."
        )
