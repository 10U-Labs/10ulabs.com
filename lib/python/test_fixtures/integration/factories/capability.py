"""Capability test factory functions."""
from botocore.exceptions import ClientError
import pytest


def create_layer6_capability_tests(capabilities: frozenset | None = None):
    """Create Layer 6 deployment capability test class.

    Args:
        capabilities: frozenset of capability names to include. Valid names:
            'lambda', 'iam', 'ssm', 'dynamodb', 'logs', 's3'.
            Defaults to frozenset({'lambda', 'iam'}) if None.

    Returns:
        Test class with Layer 6 capability tests
    """
    if capabilities is None:
        capabilities = frozenset({'lambda', 'iam'})

    class TestDeploymentCapabilities:
        """Layer 6: Verify deployment capabilities."""

        def get_enabled_capabilities(self):
            """Return the set of enabled capabilities for this test class."""
            return capabilities

        def test_capabilities_configured(self):
            """Verify at least one capability is being tested."""
            assert len(capabilities) > 0, "No capabilities configured for testing"

    if 'lambda' in capabilities:

        def test_can_list_lambda_functions(_self, lambda_client):
            """Verify we can list Lambda functions (required for deployment)."""
            try:
                lambda_client.list_functions(MaxItems=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot list Lambda functions, deployment will fail: {e}"
                )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_lambda_functions",
            test_can_list_lambda_functions,
        )

    if 'iam' in capabilities:

        def test_can_list_iam_roles(_self, iam_client):
            """Verify we can list IAM roles (required for deployment)."""
            try:
                iam_client.list_roles(MaxItems=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot list IAM roles, deployment will fail: {e}"
                )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_iam_roles",
            test_can_list_iam_roles,
        )

    if 'ssm' in capabilities:

        def test_can_describe_ssm_parameters(_self, ssm_client):
            """Verify we can describe SSM parameters (required for deployment)."""
            try:
                ssm_client.describe_parameters(MaxResults=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot describe SSM parameters, deployment will fail: {e}"
                )

        setattr(
            TestDeploymentCapabilities,
            "test_can_describe_ssm_parameters",
            test_can_describe_ssm_parameters,
        )

    if 'dynamodb' in capabilities:

        def test_can_list_dynamodb_tables(_self, dynamodb_client):
            """Verify we can list DynamoDB tables (required for deployment)."""
            try:
                dynamodb_client.list_tables(Limit=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot list DynamoDB tables, deployment will fail: {e}"
                )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_dynamodb_tables",
            test_can_list_dynamodb_tables,
        )

    if 'logs' in capabilities:

        def test_can_list_log_groups(_self, logs_client):
            """Verify we can list CloudWatch log groups (required for deployment)."""
            try:
                logs_client.describe_log_groups(limit=1)
            except ClientError as e:
                pytest.fail(
                    f"Cannot list CloudWatch log groups, deployment will fail: {e}"
                )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_log_groups",
            test_can_list_log_groups,
        )

    if 's3' in capabilities:

        def test_can_list_s3_buckets(_self, s3_client):
            """Verify we can list S3 buckets (required for deployment)."""
            try:
                s3_client.list_buckets()
            except ClientError as e:
                pytest.fail(
                    f"Cannot list S3 buckets, deployment will fail: {e}"
                )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_s3_buckets",
            test_can_list_s3_buckets,
        )

    return TestDeploymentCapabilities
