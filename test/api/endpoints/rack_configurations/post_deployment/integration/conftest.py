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


@pytest.fixture(scope="session")
def glue_client(aws_region):
    """Create a Glue client."""
    return boto3.client("glue", region_name=aws_region)


@pytest.fixture(scope="session")
def scheduler_client(aws_region):
    """Create an EventBridge Scheduler client."""
    return boto3.client("scheduler", region_name=aws_region)


@pytest.fixture(scope="session")
def events_client(aws_region):
    """Create an EventBridge client."""
    return boto3.client("events", region_name=aws_region)


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
def export_function_name(request):
    """Get the export Lambda function name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}RackConfigurationsExport"


@pytest.fixture(scope="module")
def crawler_trigger_function_name(request):
    """Get the crawler trigger Lambda function name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}RackConfigurationsCrawlerTrigger"


@pytest.fixture(scope="module")
def handler_role_name(request):
    """Get the handler IAM role name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}RackConfigurationsLambdaRole"


@pytest.fixture(scope="module")
def export_role_name(request):
    """Get the export IAM role name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}RackConfigurationsExportRole"


@pytest.fixture(scope="module")
def crawler_trigger_role_name(request):
    """Get the crawler trigger IAM role name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}RackConfigurationsCrawlerTriggerRole"


@pytest.fixture(scope="module")
def glue_crawler_role_name(request):
    """Get the Glue crawler IAM role name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}RackConfigurationsGlueCrawlerRole"


@pytest.fixture(scope="module")
def scheduler_role_name(request):
    """Get the scheduler IAM role name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}RackConfigurationsSchedulerRole"


@pytest.fixture(scope="module")
def configurations_table_name(request):
    """Get the configurations DynamoDB table name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}-rack-configurations-configurations"


@pytest.fixture(scope="module")
def events_table_name(request):
    """Get the events DynamoDB table name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}-rack-configurations-events"
