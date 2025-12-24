"""Pytest fixtures for runners post-deployment integration tests."""
import boto3
import pytest

from test_fixtures.aws import get_log_group_info

# Enable layer marker plugin for test ordering
pytest_plugins = ['pytest_layers']


@pytest.fixture(name="sqs_client", scope="session")
def sqs_client_fixture(aws_region):
    """Provide an SQS client for the configured region."""
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(name="circuit_breaker_recovery_log_group", scope="module")
def circuit_breaker_recovery_log_group_fixture(logs_client, config):
    """Get the circuit breaker recovery log group info."""
    function_name = config["circuit_breaker_recovery_function_name"]
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(name="circuit_breaker_remediation_log_group", scope="module")
def circuit_breaker_remediation_log_group_fixture(logs_client, config):
    """Get the circuit breaker remediation log group info."""
    function_name = config["circuit_breaker_remediation_function_name"]
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(name="dlq_reprocessor_log_group", scope="module")
def dlq_reprocessor_log_group_fixture(logs_client, config):
    """Get the DLQ reprocessor log group info."""
    function_name = config["dlq_reprocessor_function_name"]
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)
