"""Tests to detect Terraform state drift for echo endpoint.

These tests verify that resources Terraform plans to create don't already
exist in AWS. If they do, it indicates the resource was created outside
of Terraform or the state was lost, and needs to be imported.
"""

from pathlib import Path

from terraform_drift.test_helpers import create_orphaned_resource_tests

ECHO_SRC = (
    Path(__file__).parents[6] / "src" / "api" / "endpoints" / "echo"
)

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=ECHO_SRC,
    region="us-east-2",
)
