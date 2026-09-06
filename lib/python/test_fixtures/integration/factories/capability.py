from typing import Any

from test_fixtures.integration.helpers import aws_call_error


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
            error = aws_call_error(lambda: lambda_client.list_functions(MaxItems=1))
            assert not error, (
                f"Cannot list Lambda functions, deployment will fail: {error}"
            )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_lambda_functions",
            test_can_list_lambda_functions,
        )

    if 'iam' in enabled:

        def test_can_list_iam_roles(_self: Any, iam_client: Any) -> None:
            error = aws_call_error(lambda: iam_client.list_roles(MaxItems=1))
            assert not error, (
                f"Cannot list IAM roles, deployment will fail: {error}"
            )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_iam_roles",
            test_can_list_iam_roles,
        )

    if 'ssm' in enabled:

        def test_can_describe_ssm_parameters(_self: Any, ssm_client: Any) -> None:
            error = aws_call_error(lambda: ssm_client.describe_parameters(MaxResults=1))
            assert not error, (
                f"Cannot describe SSM parameters, deployment will fail: {error}"
            )

        setattr(
            TestDeploymentCapabilities,
            "test_can_describe_ssm_parameters",
            test_can_describe_ssm_parameters,
        )

    if 'dynamodb' in enabled:

        def test_can_list_dynamodb_tables(_self: Any, dynamodb_client: Any) -> None:
            error = aws_call_error(lambda: dynamodb_client.list_tables(Limit=1))
            assert not error, (
                f"Cannot list DynamoDB tables, deployment will fail: {error}"
            )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_dynamodb_tables",
            test_can_list_dynamodb_tables,
        )

    if 'logs' in enabled:

        def test_can_list_log_groups(_self: Any, logs_client: Any) -> None:
            error = aws_call_error(lambda: logs_client.describe_log_groups(limit=1))
            assert not error, (
                f"Cannot list CloudWatch log groups, deployment will fail: {error}"
            )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_log_groups",
            test_can_list_log_groups,
        )

    if 's3' in enabled:

        def test_can_list_s3_buckets(_self: Any, s3_client: Any) -> None:
            error = aws_call_error(s3_client.list_buckets)
            assert not error, (
                f"Cannot list S3 buckets, deployment will fail: {error}"
            )

        setattr(
            TestDeploymentCapabilities,
            "test_can_list_s3_buckets",
            test_can_list_s3_buckets,
        )

    return TestDeploymentCapabilities
