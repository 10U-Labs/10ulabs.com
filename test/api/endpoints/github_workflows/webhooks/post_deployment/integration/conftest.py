"""Pytest fixtures for runners post-deployment integration tests."""
import boto3
import pytest

from test_fixtures.aws import get_log_group_info



@pytest.fixture(name="sqs_client", scope="session")
def sqs_client_fixture(aws_region):
    """Provide an SQS client for the configured region."""
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(name="runners_handler_log_group", scope="module")
def runners_handler_log_group_fixture(logs_client, config):
    """Get the runners handler log group info."""
    function_name = config["webhook_handler_function_name"]
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(name="circuit_open_recoveries_log_group", scope="module")
def circuit_open_recoveries_log_group_fixture(logs_client, config):
    """Get the circuit open recovery log group info."""
    function_name = config["circuit_open_recoveries_function_name"]
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(name="circuit_open_remediations_log_group", scope="module")
def circuit_open_remediations_log_group_fixture(logs_client, config):
    """Get the circuit open remediation log group info."""
    function_name = config["circuit_open_remediations_function_name"]
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(name="dlq_reprocessor_log_group", scope="module")
def dlq_reprocessor_log_group_fixture(logs_client, config):
    """Get the DLQ reprocessor log group info."""
    function_name = config["dlq_reprocessor_function_name"]
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)
