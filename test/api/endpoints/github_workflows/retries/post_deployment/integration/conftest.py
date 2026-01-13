"""Shared fixtures for retries post-deployment integration tests."""
import boto3
import pytest

from test_fixtures.aws import get_log_group_info


@pytest.fixture
def function_name(res_prefix: str) -> str:
    """Provide the Lambda function name."""
    return f"{res_prefix}GitHubWorkflowsRetries"


@pytest.fixture
def queue_name(res_prefix: str) -> str:
    """Provide the SQS queue name."""
    return f"{res_prefix}GitHubWorkflowsRetries"


@pytest.fixture
def dlq_name(res_prefix: str) -> str:
    """Provide the SQS DLQ name."""
    return f"{res_prefix}GitHubWorkflowsRetriesDlq"


@pytest.fixture
def lambda_role_name(res_prefix: str) -> str:
    """Provide the Lambda IAM role name."""
    return f"{res_prefix}GitHubWorkflowsRetriesRole"


@pytest.fixture(name="sqs_client", scope="session")
def sqs_client_fixture(aws_region):
    """Provide an SQS client for the configured region."""
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(name="handler_log_group")
def handler_log_group_fixture(logs_client, function_name):
    """Get the handler log group info."""
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(name="config")
def config_fixture(shared_config, res_prefix):
    """Provide config dict for configuration and wiring tests."""
    return {
        "resource_prefix": res_prefix,
        "aws_region": shared_config["aws_region"],
        "aws_account_id": shared_config["aws_account_id"],
        "function_name": f"{res_prefix}GitHubWorkflowsRetries",
        "queue_name": f"{res_prefix}GitHubWorkflowsRetries",
        "dlq_name": f"{res_prefix}GitHubWorkflowsRetriesDlq",
        "lambda_role_name": f"{res_prefix}GitHubWorkflowsRetriesRole",
    }
