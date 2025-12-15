"""Layer 5 tests: Terraform state drift detection.

These tests detect orphaned resources - resources that exist in AWS
but are not managed by Terraform state.
"""
from pathlib import Path

from terraform_drift.test_helpers import create_orphaned_resource_tests

REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"

# Create orphaned resource tests for the agents endpoint
# This will detect resources in AWS that are not in Terraform state
TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=AGENTS_SRC,
    region="us-east-2",
)
