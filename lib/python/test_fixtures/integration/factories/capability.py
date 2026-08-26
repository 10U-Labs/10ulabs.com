from botocore.exceptions import ClientError
import pytest


def create_layer6_capability_tests(capabilities: frozenset | None = None):
    if capabilities is None:
        capabilities = frozenset({'lambda', 'iam'})

    class TestDeploymentCapabilities:
        def get_enabled_capabilities(self):
            return capabilities

        def test_capabilities_configured(self):
            assert len(capabilities) > 0, "No capabilities configured for testing"

    if 'lambda' in capabilities:

        def test_can_list_lambda_functions(_self, lambda_client):
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
