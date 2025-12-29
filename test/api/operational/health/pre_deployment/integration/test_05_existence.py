"""Layer 5: Existence tests for health endpoint pre-deployment.

Tests that prerequisite resources exist. Assumes authorization passed.
These tests verify that resources from OTHER workflows that THIS workflow
depends on exist before deployment.

Seven-layer testing model:
- Layer 5: Existence - Prerequisite resources exist
"""

import pytest
from test_fixtures.integration import Layer5APIBackendPrerequisiteTests


pytestmark = pytest.mark.layer(5)


class TestAPIBackendPrerequisites(Layer5APIBackendPrerequisiteTests):
    """Layer 5: Verify api_shared_routing prerequisites exist.

    All tests inherited from Layer5APIBackendPrerequisiteTests base class.
    """
