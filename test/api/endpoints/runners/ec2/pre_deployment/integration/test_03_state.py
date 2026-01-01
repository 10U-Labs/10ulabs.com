"""Layer 3: State tests.

Verify Terraform state matches AWS reality - resources Terraform plans to
create don't already exist in AWS.
"""
import pytest

from repo_utils import REPO_ROOT
from terraform_drift.test_helpers import create_orphaned_resource_tests

pytestmark = pytest.mark.layer(3)

EC2_RUNNER_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners" / "ec2"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=EC2_RUNNER_SRC,
    region="us-east-2",
)
