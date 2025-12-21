"""Tests to detect Terraform state drift for www/shared infrastructure.

These tests verify that resources Terraform plans to create don't already
exist in AWS. If they do, it indicates the resource was created outside
of Terraform or the state was lost, and needs to be imported.
"""

from pathlib import Path

from terraform_config import TEST_AWS_REGION
from terraform_drift.test_helpers import create_orphaned_resource_tests

WWW_SHARED_SRC = (
    Path(__file__).parents[5] / "src" / "www" / "shared"
)

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=WWW_SHARED_SRC,
    region=TEST_AWS_REGION,
)
