"""Layer 3: State validation tests for api_shared_routing pre-deployment.

Verifies Terraform state matches AWS reality. Skips in cold state (no prior state).
"""
from pathlib import Path

import pytest

from terraform_drift.test_helpers import create_orphaned_resource_tests

pytestmark = pytest.mark.layer(3)

API_BACKEND_SRC = (
    Path(__file__).parents[5] / "src" / "api" / "shared" / "routing"
)

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=API_BACKEND_SRC,
    region="us-east-2",
)
