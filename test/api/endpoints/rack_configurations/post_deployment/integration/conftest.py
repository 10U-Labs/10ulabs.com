"""Pytest fixtures for rack configurations integration tests."""
# pylint: disable=redefined-outer-name
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
def backup_role_name(request):
    """Get the backup IAM role name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}RackConfigurationsBackupRole"


@pytest.fixture(scope="module")
def backup_vault_name(request):
    """Get the backup vault name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}-rack-configurations-backup"


@pytest.fixture(scope="module")
def configurations_table_name(request):
    """Get the configurations DynamoDB table name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}-rack-configurations-configurations"


@pytest.fixture(scope="module")
def configurations_table_arn(dynamodb_client, configurations_table_name):
    """Get the configurations DynamoDB table ARN."""
    response = dynamodb_client.describe_table(TableName=configurations_table_name)
    return response["Table"]["TableArn"]


@pytest.fixture(scope="module")
def backup_plan_name(request):
    """Get the backup plan name."""
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}-rack-configurations-backup"


@pytest.fixture(scope="session")
def backup_client(aws_region):
    """Create an AWS Backup client."""
    return boto3.client("backup", region_name=aws_region)


@pytest.fixture(scope="module")
def backup_plan_id(backup_client, backup_plan_name):
    """Get the backup plan ID by name."""
    plans = backup_client.list_backup_plans()
    for plan in plans.get("BackupPlansList", []):
        if plan["BackupPlanName"] == backup_plan_name:
            return plan["BackupPlanId"]
    return None
