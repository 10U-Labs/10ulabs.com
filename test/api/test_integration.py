import json
import os
import boto3
import pytest


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
def lambda_client(aws_region):
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(scope="module")
def s3_client(aws_region):
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(scope="module")
def ec2_client(aws_region):
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(scope="module")
def ecr_client(aws_region):
    return boto3.client("ecr", region_name=aws_region)


@pytest.fixture(scope="module")
def ecs_client(aws_region):
    return boto3.client("ecs", region_name=aws_region)


def test_lambda_health_handler_exists(lambda_client):
    response = lambda_client.get_function(FunctionName="HealthHandler")
    assert response["Configuration"]["FunctionName"] == "HealthHandler"


def test_lambda_health_handler_runtime(lambda_client):
    response = lambda_client.get_function(FunctionName="HealthHandler")
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_v1_handler_exists(lambda_client):
    response = lambda_client.get_function(FunctionName="V1ApiHandler")
    assert response["Configuration"]["FunctionName"] == "V1ApiHandler"


def test_lambda_v1_handler_runtime(lambda_client):
    response = lambda_client.get_function(FunctionName="V1ApiHandler")
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_catchall_handler_exists(lambda_client):
    response = lambda_client.get_function(FunctionName="CatchAllHandler")
    assert response["Configuration"]["FunctionName"] == "CatchAllHandler"


def test_lambda_catchall_handler_runtime(lambda_client):
    response = lambda_client.get_function(FunctionName="CatchAllHandler")
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_runners_handler_exists(lambda_client, config):
    function_name = config["naming"]["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_lambda_runners_handler_runtime(lambda_client, config):
    function_name = config["naming"]["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_s3_docs_bucket_exists(s3_client, config):
    bucket_name = config["domain_names"]["subdomain"]
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_s3_bucket_versioning_disabled(s3_client, config):
    bucket_name = config["domain_names"]["subdomain"]
    response = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert response.get("Status") != "Enabled"


def test_s3_bucket_encryption_enabled(s3_client, config):
    bucket_name = config["domain_names"]["subdomain"]
    response = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert "Rules" in response


def test_index_html_in_s3(s3_client, config):
    bucket_name = config["domain_names"]["subdomain"]
    response = s3_client.head_object(Bucket=bucket_name, Key="index.html")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_openapi_yml_in_s3(s3_client, config):
    bucket_name = config["domain_names"]["subdomain"]
    response = s3_client.head_object(Bucket=bucket_name, Key="openapi.yml")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_ecr_repository_exists(ecr_client, config):
    repository_name = config["aws"]["fargate_runners"]["ecr_repository"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    assert len(response["repositories"]) == 1


def test_ecs_cluster_exists(ecs_client, config):
    cluster_name = config["naming"]["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert len(response["clusters"]) == 1


def test_ecs_cluster_status_active(ecs_client, config):
    cluster_name = config["naming"]["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert response["clusters"][0]["status"] == "ACTIVE"
