"""Shared test helpers for Terraform drift detection tests across endpoints."""

from pathlib import Path
from typing import List, Tuple

import pytest

from terraform_config import (
    extract_iam_role_names,
    extract_lambda_function_names,
)
from terraform_drift import (
    check_resource_exists,
    get_supported_resource_types,
    is_resource_in_state,
)


def create_orphaned_resource_tests(
    terraform_dir: Path,
    resources: List[Tuple[str, str, str]],
    region: str = "us-east-2",
):
    """Create test class for detecting orphaned resources.

    Args:
        terraform_dir: Path to the Terraform directory for this endpoint
        resources: List of (resource_type, resource_name, tf_address) tuples
        region: AWS region to check in

    Returns:
        Test class with parametrized tests for the given resources.
    """
    class TestOrphanedResources:
        """Tests to detect resources that exist in AWS but not in Terraform state."""

        def test_resources_configured(self):
            """Verify resources are configured for drift detection."""
            print(f"\nConfigured {len(resources)} resources for drift detection:")
            for resource_type, resource_name, _ in resources:
                print(f"  - {resource_type}: {resource_name}")
            assert resources, "No resources configured for drift detection"

        @pytest.mark.parametrize(
            "resource_type,resource_name,tf_address",
            resources,
            ids=[f"{r[0]}_{r[1]}" for r in resources],
        )
        def test_resource_not_orphaned(
            self,
            resource_type: str,
            resource_name: str,
            tf_address: str,
        ):
            """Verify resource doesn't exist in AWS when Terraform plans to create it.

            If this test fails, it means the resource exists in AWS but is not
            in Terraform state. You need to import it before applying:

                terraform import <tf_address> <resource_name>
            """
            print("\n" + "=" * 60)
            print(f"Checking: {resource_type}")
            print(f"  AWS Name: {resource_name}")
            print(f"  TF Address: {tf_address}")
            print(f"  Region: {region}")

            if resource_type not in get_supported_resource_types():
                print("  Status: SKIPPED (resource type not supported)")
                pytest.skip(f"Resource type {resource_type} not supported for drift check")

            # Check if resource is already in Terraform state
            print("  Checking Terraform state...")
            in_state = is_resource_in_state(terraform_dir, tf_address)
            print(f"  In Terraform state: {in_state}")

            if in_state:
                print("  Status: PASS (resource is managed by Terraform)")
                print("=" * 60)
                return  # Resource is in state, nothing to check

            # Resource is NOT in state - check if it exists in AWS
            print("  Checking AWS for existing resource...")
            exists = check_resource_exists(resource_type, resource_name, region)
            print(f"  Exists in AWS: {exists}")

            if exists:
                print("  Status: FAIL (orphaned resource detected)")
                print("=" * 60)
                pytest.fail(
                    f"\n\n{'!'*60}\n"
                    f"ORPHANED RESOURCE DETECTED\n"
                    f"{'!'*60}\n\n"
                    f"Resource Type: {resource_type}\n"
                    f"AWS Name: {resource_name}\n"
                    f"TF Address: {tf_address}\n\n"
                    f"This resource exists in AWS but is NOT in Terraform state.\n"
                    f"This will cause 'terraform apply' to fail or hang.\n\n"
                    f"FIX: Run the following command before applying:\n\n"
                    f"    terraform import {tf_address} {resource_name}\n\n"
                    f"{'!'*60}"
                )
            else:
                print("  Status: PASS (resource does not exist, safe to create)")
                print("=" * 60)

    return TestOrphanedResources


def get_resources_from_terraform_config(
    terraform_dir: Path,
) -> List[Tuple[str, str, str]]:
    """Extract resource definitions from Terraform files.

    Parses Terraform files to find resources that would be created,
    without running terraform plan (faster, no AWS calls).

    Args:
        terraform_dir: Path to directory containing Terraform files

    Returns:
        List of (resource_type, resource_name, tf_address) tuples
    """
    resources = []

    # Extract Lambda functions
    lambda_tf = terraform_dir / "lambda.tf"
    if lambda_tf.exists():
        for tf_name, aws_name in extract_lambda_function_names(lambda_tf, use_handler_names=True):
            resources.append((
                "aws_lambda_function",
                aws_name,
                f"aws_lambda_function.{tf_name}",
            ))

    # Extract IAM roles from iam.tf
    iam_tf = terraform_dir / "iam.tf"
    if iam_tf.exists():
        for tf_name, aws_name in extract_iam_role_names(iam_tf):
            resources.append((
                "aws_iam_role",
                aws_name,
                f"aws_iam_role.{tf_name}",
            ))

    # Extract IAM roles from analytics.tf (some endpoints have this)
    analytics_tf = terraform_dir / "analytics.tf"
    if analytics_tf.exists():
        for tf_name, aws_name in extract_iam_role_names(analytics_tf):
            resources.append((
                "aws_iam_role",
                aws_name,
                f"aws_iam_role.{tf_name}",
            ))
        # Also check for Lambda functions in analytics.tf
        lambdas = extract_lambda_function_names(analytics_tf, use_handler_names=True)
        for tf_name, aws_name in lambdas:
            resources.append((
                "aws_lambda_function",
                aws_name,
                f"aws_lambda_function.{tf_name}",
            ))

    return resources
