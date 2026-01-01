"""Layer 4: State tests for www_common pre-deployment validation.

These tests verify that resources Terraform plans to create don't already
exist in AWS. If they do, it indicates the resource was created outside
of Terraform or the state was lost, and needs to be imported.
"""
import pytest

from repo_utils import REPO_ROOT
from terraform_config import TEST_AWS_REGION
from terraform_drift.test_helpers import create_orphaned_resource_tests

pytestmark = pytest.mark.layer(4)

WWW_SHARED_SRC = REPO_ROOT / "src" / "www" / "common"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=WWW_SHARED_SRC,
    region=TEST_AWS_REGION,
)
