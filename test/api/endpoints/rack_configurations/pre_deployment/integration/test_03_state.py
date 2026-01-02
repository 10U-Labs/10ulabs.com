"""Layer 3: State tests for rack_designer endpoint pre-deployment.

Tests that Terraform state matches AWS reality. Detects resources that
exist in AWS but not in state (orphaned) or vice versa.

Six-layer testing model:
- Layer 3: State - Terraform state matches AWS reality
"""
import pytest

from repo_utils import REPO_ROOT
from terraform_drift.test_helpers import create_orphaned_resource_tests


pytestmark = pytest.mark.layer(3)

RACK_DESIGNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "rack_designer"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=RACK_DESIGNER_SRC,
    region="us-east-2",
)
