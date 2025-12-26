"""Layer 4: Existence tests for health endpoint pre-deployment.

Tests that prerequisite resources exist. Assumes authorization passed.
These tests verify that resources from OTHER workflows that THIS workflow
depends on exist before deployment.

Six-layer testing model:
- Layer 4: Existence - Prerequisite resources exist
"""

import pytest
from test_fixtures.integration import Layer4APIBackendPrerequisiteTests


pytestmark = pytest.mark.layer(4)


class TestAPIBackendPrerequisites(Layer4APIBackendPrerequisiteTests):
    """Layer 4: Verify api_shared_routing prerequisites exist.

    All tests inherited from Layer4APIBackendPrerequisiteTests base class.
    """
