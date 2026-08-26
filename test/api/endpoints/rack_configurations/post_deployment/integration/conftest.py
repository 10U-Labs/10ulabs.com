import boto3
import pytest

from test_fixtures.aws import get_log_group_info


@pytest.fixture(scope="module")
def website_url(config):
    return f"https://www.{config['domain_name']}"


@pytest.fixture(scope="module")
def handler_log_group(logs_client, shared_config):
    function_name = shared_config.get("lambda_handler_names", {}).get(
        "rack_configurations", "TenULabsRackConfigurationsHandler"
    )
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(scope="module")
def test_device_id():
    return "integration-test-device"


@pytest.fixture(scope="session")
def dynamodb_client(aws_region):
    return boto3.client("dynamodb", region_name=aws_region)


@pytest.fixture(scope="module")
def resource_prefix(shared_config):
    return shared_config.get("resource_prefix", "TenULabs")


@pytest.fixture(scope="module")
def handler_function_name(shared_config):
    return shared_config.get("lambda_handler_names", {}).get(
        "rack_configurations", "TenULabsRackConfigurationsHandler"
    )


@pytest.fixture(scope="module")
def handler_role_name(request):
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}RackConfigurationsLambdaRole"


@pytest.fixture(scope="module")
def backup_role_name(request):
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}RackConfigurationsBackupRole"


@pytest.fixture(scope="module")
def backup_vault_name(request):
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}-rack-configurations-backup"


@pytest.fixture(scope="module")
def configurations_table_name(request):
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}-rack-configurations-configurations"


@pytest.fixture(scope="module")
def configurations_table_arn(request):
    client = request.getfixturevalue("dynamodb_client")
    table_name = request.getfixturevalue("configurations_table_name")
    response = client.describe_table(TableName=table_name)
    return response["Table"]["TableArn"]


@pytest.fixture(scope="module")
def backup_plan_name(request):
    prefix = request.getfixturevalue("resource_prefix")
    return f"{prefix}-rack-configurations-backup"


@pytest.fixture(scope="session")
def backup_client(aws_region):
    return boto3.client("backup", region_name=aws_region)


@pytest.fixture(scope="module")
def backup_plan_id(request):
    client = request.getfixturevalue("backup_client")
    plan_name = request.getfixturevalue("backup_plan_name")
    plans = client.list_backup_plans()
    for plan in plans.get("BackupPlansList", []):
        if plan["BackupPlanName"] == plan_name:
            return plan["BackupPlanId"]
    return None
