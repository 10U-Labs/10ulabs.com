"""Pytest fixtures for rack configurations integration tests."""
import boto3
import pytest

from test_fixtures.aws import get_log_group_info


@pytest.fixture(name="website_url", scope="module")
def website_url_fixture(config):
    """Provide website URL for tests."""
    return f"https://www.{config['domain_name']}"


@pytest.fixture(name="handler_log_group", scope="module")
def handler_log_group_fixture(logs_client, shared_config):
    """Get the rack configurations handler log group info from CloudWatch."""
    function_name = shared_config.get("lambda_handler_names", {}).get(
        "rack_configurations", "TenULabsRackConfigurationsHandler"
    )
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(name="test_device_id", scope="module")
def test_device_id_fixture():
    """Provide test device ID for tests."""
    return "integration-test-device"


@pytest.fixture(scope="session")
def dynamodb_client(aws_region):
    """Create a DynamoDB client."""
    return boto3.client("dynamodb", region_name=aws_region)


@pytest.fixture(scope="module")
def resource_prefix(shared_config):
    """Get the resource prefix for rack configurations resources."""
    return shared_config.get("resource_prefix", "TenULabs")


@pytest.fixture(scope="module")
def handler_function_name(shared_config):
    """Get the handler Lambda function name."""
    return shared_config.get("lambda_handler_names", {}).get(
        "rack_configurations", "TenULabsRackConfigurationsHandler"
    )


@pytest.fixture(scope="module")
def handler_role_name(request):
    """Get the handler IAM role name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}RackConfigurationsLambdaRole"


@pytest.fixture(scope="module")
def configurations_table_name(request):
    """Get the configurations DynamoDB table name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}-rack-configurations-configurations"
