"""Layer 3: State - Does Terraform state match AWS reality?

These tests verify that Terraform state is consistent with AWS. Resources that
Terraform plans to create should not already exist in AWS (orphan detection).

Six-layer testing model:
- Layer 1: Authentication - Are credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: State - Does Terraform state match AWS reality? (THIS FILE)
- Layer 4: Existence - Do the required resources exist?
- Layer 5: Configuration - Are resources configured correctly?
- Layer 6: Capability - Can we perform required operations?
"""
from pathlib import Path

import pytest

from terraform_drift.test_helpers import create_orphaned_resource_tests


pytestmark = pytest.mark.layer(3)

TERRAFORM_DIR = Path(__file__).parents[6] / "src" / "api" / "endpoints" / "runners"


# Use the factory from terraform_drift to create orphan detection tests
TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=TERRAFORM_DIR,
    region="us-east-2",
)
