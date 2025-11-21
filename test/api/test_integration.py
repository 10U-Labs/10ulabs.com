import boto3
import pytest


@pytest.fixture(scope="module")
def aws_region():
    return "us-east-1"


@pytest.fixture(scope="module")
def lambda_client(aws_region):
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(scope="module")
def s3_client(aws_region):
    return boto3.client("s3", region_name=aws_region)


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


def test_s3_docs_bucket_exists(s3_client):
    bucket_name = "api.10ulabs.com"
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_s3_bucket_versioning_disabled(s3_client):
    bucket_name = "api.10ulabs.com"
    response = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert response.get("Status") != "Enabled"


def test_s3_bucket_encryption_enabled(s3_client):
    bucket_name = "api.10ulabs.com"
    response = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert "ServerSideEncryptionConfiguration" in response
    assert "Rules" in response["ServerSideEncryptionConfiguration"]


def test_index_html_in_s3(s3_client):
    bucket_name = "api.10ulabs.com"
    response = s3_client.head_object(Bucket=bucket_name, Key="index.html")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_openapi_yml_in_s3(s3_client):
    bucket_name = "api.10ulabs.com"
    response = s3_client.head_object(Bucket=bucket_name, Key="openapi.yml")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_lambda_runners_handler_exists(lambda_client):
    function_name = "TenULabsWebhookHandler"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_lambda_runners_handler_runtime(lambda_client):
    function_name = "TenULabsWebhookHandler"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_ecr_repository_exists(ecr_client):
    repository_name = "github-runner"
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    assert len(response["repositories"]) == 1


def test_ecs_cluster_exists(ecs_client):
    cluster_name = "TenULabsRunnerCluster"
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert len(response["clusters"]) == 1


def test_ecs_cluster_status_active(ecs_client):
    cluster_name = "TenULabsRunnerCluster"
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert response["clusters"][0]["status"] == "ACTIVE"
