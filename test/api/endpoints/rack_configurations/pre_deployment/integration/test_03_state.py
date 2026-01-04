"""Layer 3: State tests for rack_configurations endpoint pre-deployment.

Tests that Terraform state matches AWS reality. Detects resources that
exist in AWS but not in state (orphaned) or vice versa.

Six-layer testing model:
- Layer 3: State - Terraform state matches AWS reality
"""

from repo_utils import REPO_ROOT
from terraform_drift.test_helpers import create_orphaned_resource_tests



RACK_CONFIGURATIONS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "rack_configurations"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=RACK_CONFIGURATIONS_SRC,
    region="us-east-2",
)
