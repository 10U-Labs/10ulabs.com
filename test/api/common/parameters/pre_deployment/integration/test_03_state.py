"""Layer 3: State tests for api/common/parameters pre-deployment.

Tests that Terraform state exists and is accessible.

Six-layer testing model:
- Layer 3: State - Terraform state accessible
"""

import pytest
from test_fixtures.integration import Layer4TerraformStateExistenceTests


pytestmark = pytest.mark.layer(3)


class TestTerraformState(Layer4TerraformStateExistenceTests):
    """Layer 3: Verify Terraform state is accessible."""
