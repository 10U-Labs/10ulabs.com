"""Layer 3: State tests.

Verify Terraform state matches AWS reality - resources Terraform plans to
create don't already exist in AWS.
"""
from pathlib import Path

import pytest

from terraform_drift.test_helpers import create_orphaned_resource_tests

pytestmark = pytest.mark.layer(3)

EC2_RUNNER_SRC = (
    Path(__file__).parents[7] / "src" / "api" / "endpoints" / "runners" / "ec2"
)

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=EC2_RUNNER_SRC,
    region="us-east-2",
)
