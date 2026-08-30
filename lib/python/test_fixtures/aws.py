from datetime import datetime, timedelta, timezone
from typing import Optional

import boto3
from botocore.exceptions import ClientError
import pytest
from terraform_config import get_shared_config


@pytest.fixture(scope="session")
def shared_config():
    return get_shared_config()


@pytest.fixture(scope="session")
def aws_region(request):
    config = request.getfixturevalue("shared_config")
    return config["aws_region"]


@pytest.fixture(scope="session")
def state_bucket_name(request):
    config = request.getfixturevalue("shared_config")
    return config["name_for_terraform_state_bucket"]


@pytest.fixture(scope="session")
def sts_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("sts", region_name=region)


@pytest.fixture(scope="session")
def iam_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("iam", region_name=region)


@pytest.fixture(scope="session")
def s3_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("s3", region_name=region)


@pytest.fixture(scope="session")
def ssm_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("ssm", region_name=region)


@pytest.fixture(scope="session")
def logs_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("logs", region_name=region)


def iam_role_exists(client, role_name: str) -> bool:
    try:
        client.get_role(RoleName=role_name)
        return True
    except client.exceptions.NoSuchEntityException:
        return False


def get_log_group_info(client, log_group_name: str) -> dict:
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


def find_lifecycle_rule(client, bucket_name: str, rule_id: str) -> Optional[dict]:
    lifecycle = client.get_bucket_lifecycle_configuration(Bucket=bucket_name)
    for rule in lifecycle["Rules"]:
        if rule.get("ID") == rule_id:
            return rule
    return None


def stale_delete_markers(client, bucket_name: str, older_than_days: int = 7) -> list:
    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)
    stale: list = []
    paginator = client.get_paginator("list_object_versions")
    for page in paginator.paginate(Bucket=bucket_name):
        for marker in page.get("DeleteMarkers", []):
            if marker["LastModified"] < cutoff:
                stale.append(marker["Key"])
    return stale


@pytest.fixture(scope="session")
def caller_identity(request):
    client = request.getfixturevalue("sts_client")
    return client.get_caller_identity()


@pytest.fixture(scope="session")
def _current_role_arn(request):
    identity = request.getfixturevalue("caller_identity")
    arn = identity.get("Arn", "")
    if ":assumed-role/" in arn:
        account = identity.get("Account", "")
        role_name = arn.split("/")[1]
        return f"arn:aws:iam::{account}:role/{role_name}"
    return arn


@pytest.fixture(scope="session")
def current_role_name(request):
    role_arn = request.getfixturevalue("_current_role_arn")
    if not role_arn:
        return ""
    return role_arn.split("/")[-1]


@pytest.fixture(scope="session")
def lambda_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("lambda", region_name=region)


@pytest.fixture(scope="session")
def apigateway_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("apigateway", region_name=region)


@pytest.fixture(scope="session")
def dynamodb_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("dynamodb", region_name=region)


@pytest.fixture(scope="session")
def ec2_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("ec2", region_name=region)


@pytest.fixture(scope="session")
def ses_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("ses", region_name=region)


@pytest.fixture(scope="session")
def scheduler_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("scheduler", region_name=region)


@pytest.fixture(scope="session")
def backup_client(request):
    region = request.getfixturevalue("aws_region")
    return boto3.client("backup", region_name=region)


@pytest.fixture(scope="module")
def api_gateway_info(request):
    client = request.getfixturevalue("apigateway_client")
    api_common_routing_outputs = request.getfixturevalue("api_common_routing_outputs")

    api_id = api_common_routing_outputs.get("api_gateway_id")
    if not api_id:
        return {"id": None, "exists": False, "accessible": False}

    try:
        response = client.get_rest_api(restApiId=api_id)
        endpoint_config = response.get("endpointConfiguration", {})
        paginator = client.get_paginator("get_resources")
        paths = []
        for page in paginator.paginate(restApiId=api_id):
            paths.extend([r.get("path", "") for r in page.get("items", [])])
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


@pytest.fixture(scope="module")
def api_url(request):
    config = request.getfixturevalue("config")
    return f"https://{config['api_fqdn']}"


@pytest.fixture(scope="module")
def api_key(request):
    client = request.getfixturevalue("ssm_client")
    param_response = client.get_parameter(Name='/api/key', WithDecryption=True)
    return param_response['Parameter']['Value'] if param_response else None
