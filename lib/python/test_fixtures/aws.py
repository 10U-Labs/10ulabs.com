"""AWS fixtures for pytest tests.

Use by adding to conftest.py:
    pytest_plugins = ['test_fixtures.aws']
"""
import boto3
from botocore.exceptions import ClientError
import pytest
from terraform_config import get_shared_config


@pytest.fixture(scope="session")
def shared_config():
    """Provide parsed configuration from the shared Terraform module."""
    return get_shared_config()


@pytest.fixture(scope="session")
def aws_region(request):
    """Provide the AWS region from shared config."""
    config = request.getfixturevalue("shared_config")
    return config["aws_region"]


@pytest.fixture(scope="session")
def ssm_github_pat_name(request):
    """Provide the SSM parameter name for GitHub PAT."""
    config = request.getfixturevalue("shared_config")
    return config["ssm_github_pat_name"]


@pytest.fixture(scope="session")
def state_bucket_name(request):
    """Provide the Terraform state bucket name."""
    config = request.getfixturevalue("shared_config")
    return config["name_for_terraform_state_bucket"]


@pytest.fixture(scope="session")
def sts_client(request):
    """Create an STS client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("sts", region_name=region)


@pytest.fixture(scope="session")
def iam_client(request):
    """Create an IAM client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("iam", region_name=region)


@pytest.fixture(scope="session")
def s3_client(request):
    """Create an S3 client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("s3", region_name=region)


@pytest.fixture(scope="session")
def ssm_client(request):
    """Create an SSM client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("ssm", region_name=region)


@pytest.fixture(scope="session")
def kms_client(request):
    """Create a KMS client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("kms", region_name=region)


@pytest.fixture(scope="session")
def ecr_client(request):
    """Create an ECR client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("ecr", region_name=region)


@pytest.fixture(scope="session")
def logs_client(request):
    """Create a CloudWatch Logs client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("logs", region_name=region)


def get_log_group_info(client, log_group_name: str) -> dict:
    """Get CloudWatch log group info.

    Args:
        client: CloudWatch Logs boto3 client
        log_group_name: Full log group name (e.g., /aws/lambda/MyFunction)

    Returns dict with keys: name, exists, retention.
    Use this helper in endpoint-specific log group fixtures.
    """
    response = client.describe_log_groups(
        logGroupNamePrefix=log_group_name,
        limit=1
    )
    log_groups = response.get("logGroups", [])
    matching = [lg for lg in log_groups if lg["logGroupName"] == log_group_name]
    return {
        "name": log_group_name,
        "exists": len(matching) > 0,
        "retention": matching[0].get("retentionInDays") if matching else None
    }


@pytest.fixture(scope="session")
def caller_identity(request):
    """Get the current caller identity."""
    client = request.getfixturevalue("sts_client")
    return client.get_caller_identity()


@pytest.fixture(scope="session")
def current_role_arn(request):
    """Extract the role ARN from caller identity."""
    identity = request.getfixturevalue("caller_identity")
    arn = identity.get("Arn", "")
    # Convert assumed-role ARN to role ARN
    # arn:aws:sts::123:assumed-role/role-name/session -> arn:aws:iam::123:role/role-name
    if ":assumed-role/" in arn:
        account = identity.get("Account", "")
        role_name = arn.split("/")[1]
        return f"arn:aws:iam::{account}:role/{role_name}"
    return arn


@pytest.fixture(scope="session")
def current_role_name(request):
    """Extract the role name from the role ARN."""
    role_arn = request.getfixturevalue("current_role_arn")
    if not role_arn:
        return ""
    return role_arn.split("/")[-1]


@pytest.fixture(scope="session")
def ecr_repository_name(request):
    """Provide the ECR repository name for agents."""
    config = request.getfixturevalue("shared_config")
    return config["ecr_repository_name_agents"]


@pytest.fixture(scope="session")
def lambda_client(request):
    """Create a Lambda client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("lambda", region_name=region)


@pytest.fixture(scope="session")
def apigateway_client(request):
    """Create an API Gateway client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("apigateway", region_name=region)


@pytest.fixture(scope="session")
def dynamodb_client(request):
    """Create a DynamoDB client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("dynamodb", region_name=region)


@pytest.fixture(scope="session")
def ecs_client(request):
    """Create an ECS client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("ecs", region_name=region)


@pytest.fixture(scope="session")
def ec2_client(request):
    """Create an EC2 client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("ec2", region_name=region)


@pytest.fixture(scope="session")
def ses_client(request):
    """Create an SES client."""
    region = request.getfixturevalue("aws_region")
    return boto3.client("ses", region_name=region)


@pytest.fixture(scope="session")
def state_bucket_region(request):
    """Provide the AWS region for the state bucket."""
    return request.getfixturevalue("aws_region")


@pytest.fixture(scope="module")
def api_gateway_info(request):
    """Get API Gateway info, handling missing/not-found cases gracefully.

    Requires `apigateway_client` and `api_shared_routing_outputs` fixtures.
    """
    client = request.getfixturevalue("apigateway_client")
    api_shared_routing_outputs = request.getfixturevalue("api_shared_routing_outputs")

    api_id = api_shared_routing_outputs.get("api_gateway_rest_api_id")
    if not api_id:
        return {"id": None, "exists": False, "accessible": False}

    try:
        response = client.get_rest_api(restApiId=api_id)
        endpoint_config = response.get("endpointConfiguration", {})
        resources_response = client.get_resources(restApiId=api_id)
        paths = [r.get("path", "") for r in resources_response.get("items", [])]
        return {
            "id": api_id,
            "exists": True,
            "accessible": True,
            "endpoint_types": endpoint_config.get("types", []),
            "paths": paths
        }
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDeniedException":
            return {"id": api_id, "exists": None, "accessible": False}
        if error_code == "NotFoundException":
            return {"id": api_id, "exists": False, "accessible": True}
        raise


@pytest.fixture(name="api_url", scope="module")
def api_url_fixture(request):
    """Provide the API URL from config.

    Requires a 'config' fixture with 'api_fqdn' key.
    """
    config = request.getfixturevalue("config")
    return f"https://{config['api_fqdn']}"


@pytest.fixture(name="api_key", scope="module")
def api_key_fixture(request):
    """Retrieve the API key from SSM Parameter Store.

    Requires 'ssm_client' fixture.
    """
    client = request.getfixturevalue("ssm_client")
    param_response = client.get_parameter(Name='/api/key', WithDecryption=True)
    return param_response['Parameter']['Value'] if param_response else None
