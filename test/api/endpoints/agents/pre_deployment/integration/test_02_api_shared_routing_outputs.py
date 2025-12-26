"""Layer 3-4 tests: Verify API backend outputs exist.

These tests verify that resources from the api_shared_routing workflow exist,
which is a dependency for the agents endpoint.
"""

import pytest
from repo_utils import REPO_ROOT

API_BACKEND_SRC = REPO_ROOT / "src" / "api" / "backend"


class TestAPIBackendOutputsExist:
    """Layer 3: Verify API backend outputs exist."""

    def test_api_shared_routing_terraform_exists(self):
        """Verify API backend terraform directory exists."""
        assert API_BACKEND_SRC.exists(), (
            "API backend source directory not found. "
            f"Expected at: {API_BACKEND_SRC}"
        )

    def test_api_shared_routing_has_outputs(self):
        """Verify API backend has outputs.tf file."""
        outputs_file = API_BACKEND_SRC / "outputs.tf"
        assert outputs_file.exists(), (
            "API backend outputs.tf not found. "
            "The agents endpoint depends on api_shared_routing outputs."
        )
