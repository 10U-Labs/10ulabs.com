"""Layer 3: State tests for api/common/docker_repository pre-deployment.

Tests that Terraform state matches AWS reality. Resources Terraform plans
to create should not already exist in AWS.

Six-layer testing model:
- Layer 3: State - Terraform state matches AWS reality
"""

from repo_utils import REPO_ROOT
from terraform_config import get_shared_config
from terraform_drift.test_helpers import create_orphaned_resource_tests




API_COMMON_DOCKER_REPOSITORY_SRC = REPO_ROOT / "src" / "api" / "common" / "docker_repository"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=API_COMMON_DOCKER_REPOSITORY_SRC,
    region=get_shared_config()["aws_region"],
)
