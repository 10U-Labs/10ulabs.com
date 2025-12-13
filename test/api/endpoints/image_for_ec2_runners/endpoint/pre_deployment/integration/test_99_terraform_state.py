"""Tests to detect Terraform state drift for image_for_ec2_runners endpoint.

These tests verify that resources Terraform plans to create don't already
exist in AWS. If they do, it indicates the resource was created outside
of Terraform or the state was lost, and needs to be imported.
"""

from pathlib import Path

from terraform_drift.test_helpers import create_orphaned_resource_tests

IMAGE_FOR_EC2_RUNNERS_SRC = (
    Path(__file__).parents[7] / "src" / "api" / "endpoints" / "image_for_ec2_runners"
)

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=IMAGE_FOR_EC2_RUNNERS_SRC,
    region="us-east-2",
)
