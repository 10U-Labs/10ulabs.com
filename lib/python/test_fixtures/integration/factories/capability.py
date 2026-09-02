from typing import Any

from botocore.exceptions import ClientError
import pytest


def create_layer6_capability_tests(capabilities: frozenset | None = None) -> type:
    enabled: frozenset = (
        capabilities if capabilities is not None else frozenset({'lambda', 'iam'})
    )

    class TestDeploymentCapabilities:
        def get_enabled_capabilities(self) -> frozenset:
            return enabled

        def test_capabilities_configured(self) -> None:
            assert len(enabled) > 0, "No capabilities configured for testing"

    if 'lambda' in enabled:

        def test_can_list_lambda_functions(_self: Any, lambda_client: Any) -> None:
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

    if 'iam' in enabled:

        def test_can_list_iam_roles(_self: Any, iam_client: Any) -> None:
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

    if 'ssm' in enabled:

        def test_can_describe_ssm_parameters(_self: Any, ssm_client: Any) -> None:
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

    if 'dynamodb' in enabled:

        def test_can_list_dynamodb_tables(_self: Any, dynamodb_client: Any) -> None:
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

    if 'logs' in enabled:

        def test_can_list_log_groups(_self: Any, logs_client: Any) -> None:
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

    if 's3' in enabled:

        def test_can_list_s3_buckets(_self: Any, s3_client: Any) -> None:
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
