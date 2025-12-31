"""Layer 4: Existence tests for api/common/parameters pre-deployment.

Tests that prerequisite resources exist. Assumes authorization passed.

Six-layer testing model:
- Layer 4: Existence - Resource actually exists
"""

import pytest
from test_fixtures.integration import Layer4PrerequisiteExistenceTests


pytestmark = pytest.mark.layer(4)


class TestPrerequisiteResourcesExist(Layer4PrerequisiteExistenceTests):
    """Layer 4: Verify prerequisite resources exist."""
