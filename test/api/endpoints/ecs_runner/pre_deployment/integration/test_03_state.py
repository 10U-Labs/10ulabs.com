"""Layer 3: Terraform state tests.

Verify that resources Terraform plans to create don't already
exist in AWS. If they do, it indicates the resource was created outside
of Terraform or the state was lost, and needs to be imported.
"""
from pathlib import Path

import pytest

from terraform_drift.test_helpers import create_orphaned_resource_tests

pytestmark = pytest.mark.layer(3)

ECS_RUNNER_SRC = (
    Path(__file__).parents[6] / "src" / "api" / "endpoints" / "ecs_runner"
)

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=ECS_RUNNER_SRC,
    region="us-east-2",
)
