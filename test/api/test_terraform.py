import json
import os
import subprocess
import requests
import boto3
import pytest


@pytest.fixture(scope="module")
def terraform_outputs():
    result = subprocess.run(
        ["terraform", "output", "-json"],
        cwd=os.path.join(os.path.dirname(__file__), "../../src/api/terraform"),
        capture_output=True,
        text=True,
        check=True
    )
    outputs = json.loads(result.stdout)
    return {key: value["value"] for key, value in outputs.items()}


@pytest.fixture(scope="module")
def config():
    config_path = os.path.join(os.path.dirname(__file__), "../../src/api/config.json")
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def aws_region(config):
    return config["aws"]["region"]


@pytest.fixture(scope="module")
def aws_account_id(config):
    return str(config["aws"]["account_id"])


@pytest.fixture(scope="module")
def api_url(terraform_outputs):
    return terraform_outputs["api_endpoint"]


@pytest.fixture(scope="module")
def cloudformation_client(aws_region):
    return boto3.client("cloudformation", region_name=aws_region)


@pytest.fixture(scope="module")
def lambda_client(aws_region):
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(scope="module")
def s3_client(aws_region):
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(scope="module")
def ec2_client(aws_region):
    return boto3.client("ec2", region_name=aws_region)


def test_terraform_outputs_exist(terraform_outputs):
    assert terraform_outputs is not None


def test_api_endpoint_in_outputs(terraform_outputs):
    assert "api_endpoint" in terraform_outputs


def test_vpc_id_in_outputs(terraform_outputs):
    assert "vpc_id" in terraform_outputs


def test_vpc_exists(ec2_client, terraform_outputs):
    vpc_id = terraform_outputs["vpc_id"]
    response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
    assert len(response["Vpcs"]) == 1


def test_public_subnets_exist(ec2_client, terraform_outputs):
    subnet_ids = terraform_outputs["vpc_public_subnet_ids"].split(",")
    response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
    assert len(response["Subnets"]) == len(subnet_ids)


def test_lambda_health_handler_exists(lambda_client):
    response = lambda_client.get_function(FunctionName="HealthHandler")
    assert response["Configuration"]["FunctionName"] == "HealthHandler"


def test_lambda_v1_handler_exists(lambda_client):
    response = lambda_client.get_function(FunctionName="V1ApiHandler")
    assert response["Configuration"]["FunctionName"] == "V1ApiHandler"


def test_lambda_catchall_handler_exists(lambda_client):
    response = lambda_client.get_function(FunctionName="CatchAllHandler")
    assert response["Configuration"]["FunctionName"] == "CatchAllHandler"


def test_lambda_runners_handler_exists(lambda_client, config):
    function_name = config["naming"]["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_s3_docs_bucket_exists(s3_client, config):
    bucket_name = config["domain_names"]["subdomain"]
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_s3_bucket_versioning_disabled(s3_client, config):
    bucket_name = config["domain_names"]["subdomain"]
    response = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert response.get("Status") != "Enabled"


def test_index_html_in_s3(s3_client, config):
    bucket_name = config["domain_names"]["subdomain"]
    response = s3_client.head_object(Bucket=bucket_name, Key="index.html")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_openapi_yml_in_s3(s3_client, config):
    bucket_name = config["domain_names"]["subdomain"]
    response = s3_client.head_object(Bucket=bucket_name, Key="openapi.yml")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_health_endpoint_responds(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.status_code == 200


def test_health_endpoint_returns_json(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    assert response.headers["Content-Type"] == "application/json"


def test_health_endpoint_status_healthy(api_url):
    response = requests.get(f"{api_url}/health", timeout=10)
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint_responds(api_url):
    response = requests.get(api_url, timeout=10)
    assert response.status_code == 200


def test_invalid_endpoint_returns_404(api_url):
    response = requests.get(f"{api_url}/nonexistent", timeout=10)
    assert response.status_code == 404


def test_ecr_repository_exists(terraform_outputs):
    assert "ecr_repository_name" in terraform_outputs


def test_ecs_cluster_exists(terraform_outputs):
    assert "cluster_arn" in terraform_outputs


def test_task_definition_exists(terraform_outputs):
    assert "task_definition_arn" in terraform_outputs


def test_security_group_exists(terraform_outputs):
    assert "runner_security_group_id" in terraform_outputs
