"""Layer 4: State tests for health endpoint pre-deployment.

Tests that Terraform state matches AWS reality. Resources Terraform plans
to create should not already exist. If they do, it indicates the resource
was created outside of Terraform or the state was lost, and needs to be imported.

Seven-layer testing model:
- Layer 4: State - Terraform state matches AWS reality
"""

from pathlib import Path

import pytest
from terraform_drift.test_helpers import create_orphaned_resource_tests


pytestmark = pytest.mark.layer(4)

HEALTH_SRC = (
    Path(__file__).parents[6] / "src" / "api" / "operational" / "health"
)

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=HEALTH_SRC,
    region="us-east-2",
)
