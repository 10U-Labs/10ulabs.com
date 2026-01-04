"""Layer 4: State tests for soc_simulations endpoint.

Tests that Terraform state matches AWS reality. Resources Terraform plans
to create should not already exist. Uses terraform_drift to detect orphaned
resources that need to be imported.
"""
import pytest

from repo_utils import REPO_ROOT
from terraform_drift.test_helpers import create_orphaned_resource_tests

pytestmark = pytest.mark.layer(4)

SOC_SIMULATIONS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "soc_simulations"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=SOC_SIMULATIONS_SRC,
    region="us-east-2",
)
