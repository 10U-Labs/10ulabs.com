"""Layer 4: State validation tests for api_shared_routing pre-deployment.

Verifies Terraform state matches AWS reality. Skips in cold state (no prior state).
"""
import pytest

from repo_utils import REPO_ROOT
from terraform_drift.test_helpers import create_orphaned_resource_tests

pytestmark = pytest.mark.layer(4)

API_BACKEND_SRC = REPO_ROOT / "src" / "api" / "shared" / "routing"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=API_BACKEND_SRC,
    region="us-east-2",
)
