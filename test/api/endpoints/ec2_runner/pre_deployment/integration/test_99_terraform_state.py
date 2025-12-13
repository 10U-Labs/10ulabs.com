"""Tests to detect Terraform state drift for ec2_runner endpoint.

These tests verify that resources Terraform plans to create don't already
exist in AWS. If they do, it indicates the resource was created outside
of Terraform or the state was lost, and needs to be imported.
"""

from pathlib import Path

from terraform_drift.test_helpers import create_orphaned_resource_tests

EC2_RUNNER_SRC = (
    Path(__file__).parents[6] / "src" / "api" / "endpoints" / "ec2_runner"
)

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=EC2_RUNNER_SRC,
    region="us-east-2",
)
