"""Layer 3: State tests for api/shared/runners pre-deployment.

Tests that Terraform state matches AWS reality. Resources Terraform plans
to create should not already exist in AWS.

Six-layer testing model:
- Layer 3: State - Terraform state matches AWS reality
"""

from pathlib import Path

import pytest

from terraform_drift.test_helpers import create_orphaned_resource_tests


pytestmark = pytest.mark.layer(3)


API_SHARED_RUNNERS_SRC = (
    Path(__file__).parents[5] / "src" / "api" / "shared" / "runners"
)

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=API_SHARED_RUNNERS_SRC,
    region="us-east-2",
)
