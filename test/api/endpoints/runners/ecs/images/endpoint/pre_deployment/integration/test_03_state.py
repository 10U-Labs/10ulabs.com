"""Layer 3: Terraform state tests.

Verify that resources Terraform plans to create don't already
exist in AWS. If they do, it indicates the resource was created outside
of Terraform or the state was lost, and needs to be imported.
"""
from pathlib import Path

import pytest

from terraform_drift.test_helpers import create_orphaned_resource_tests

pytestmark = pytest.mark.layer(3)

IMAGE_FOR_ECS_RUNNERS_SRC = (
    Path(__file__).parents[7] / "src" / "api" / "endpoints" / "runners" / "ecs" / "images"
)

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=IMAGE_FOR_ECS_RUNNERS_SRC,
    region="us-east-2",
)
