import os
import urllib.request
import json
import boto3
import pytest


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(tfvars):
    return tfvars["aws_region"]


@pytest.fixture(name="lambda_client", scope="module")
def lambda_client_fixture(aws_region):
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(name="s3_client", scope="module")
def s3_client_fixture(aws_region):
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(name="ecr_client", scope="module")
def ecr_client_fixture(aws_region):
    return boto3.client("ecr", region_name=aws_region)


@pytest.fixture(name="ecs_client", scope="module")
def ecs_client_fixture(aws_region):
    return boto3.client("ecs", region_name=aws_region)


@pytest.fixture(name="ssm_client", scope="module")
def ssm_client_fixture(aws_region):
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(name="github_pat", scope="module")
def github_pat_fixture():
    pat = os.environ.get("GITHUB_PAT")
    assert pat is not None
    return pat


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


def test_s3_docs_bucket_exists(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_s3_bucket_versioning_disabled(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert response.get("Status") != "Enabled"


def test_s3_bucket_encryption_enabled(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert "ServerSideEncryptionConfiguration" in response
    assert "Rules" in response["ServerSideEncryptionConfiguration"]


def test_index_html_in_s3(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.head_object(Bucket=bucket_name, Key="index.html")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_openapi_yml_in_s3(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.head_object(Bucket=bucket_name, Key="openapi.yml")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_lambda_runners_handler_exists(lambda_client, tfvars):
    function_name = tfvars["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_lambda_runners_handler_runtime(lambda_client, tfvars):
    function_name = tfvars["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_ecr_repository_exists(ecr_client, tfvars):
    repository_name = tfvars["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    assert len(response["repositories"]) == 1


def test_ecs_cluster_exists(ecs_client, tfvars):
    cluster_name = tfvars["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert len(response["clusters"]) == 1


def test_ecs_cluster_status_active(ecs_client, tfvars):
    cluster_name = tfvars["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert response["clusters"][0]["status"] == "ACTIVE"


def test_webhook_secret_parameter_exists(ssm_client, tfvars):
    webhook_secret_name = tfvars["webhook_secret_name"]
    response = ssm_client.get_parameter(Name=webhook_secret_name)
    assert response["Parameter"]["Name"] == webhook_secret_name


def test_webhook_secret_parameter_type(ssm_client, tfvars):
    webhook_secret_name = tfvars["webhook_secret_name"]
    response = ssm_client.get_parameter(Name=webhook_secret_name)
    assert response["Parameter"]["Type"] == "String"


def test_webhook_secret_parameter_value_not_placeholder(ssm_client, tfvars):
    webhook_secret_name = tfvars["webhook_secret_name"]
    response = ssm_client.get_parameter(Name=webhook_secret_name, WithDecryption=True)
    assert response["Parameter"]["Value"] != "PLACEHOLDER_WILL_BE_UPDATED"


def test_repository_has_at_least_one_webhook(github_pat, tfvars):
    url = f"https://api.github.com/repos/{tfvars['github_repo']}/hooks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {github_pat}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as response:
        hooks = json.loads(response.read())
    assert len(hooks) > 0


def test_github_webhook_for_runners_endpoint_exists(github_pat, tfvars):
    url = f"https://api.github.com/repos/{tfvars['github_repo']}/hooks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {github_pat}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as response:
        hooks = json.loads(response.read())
    webhook_url = f"https://{tfvars['domain_subdomain']}/v1/runners"
    matching_hooks = [hook for hook in hooks if hook["config"]["url"] == webhook_url]
    assert len(matching_hooks) == 1


def test_github_webhook_for_runners_endpoint_listens_for_workflow_job_events(github_pat, tfvars):
    url = f"https://api.github.com/repos/{tfvars['github_repo']}/hooks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {github_pat}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as response:
        hooks = json.loads(response.read())
    webhook_url = f"https://{tfvars['domain_subdomain']}/v1/runners"
    matching_hooks = [hook for hook in hooks if hook["config"]["url"] == webhook_url]
    assert "workflow_job" in matching_hooks[0]["events"]


def test_github_webhook_for_runners_endpoint_is_active(github_pat, tfvars):
    url = f"https://api.github.com/repos/{tfvars['github_repo']}/hooks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {github_pat}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as response:
        hooks = json.loads(response.read())
    webhook_url = f"https://{tfvars['domain_subdomain']}/v1/runners"
    matching_hooks = [hook for hook in hooks if hook["config"]["url"] == webhook_url]
    assert matching_hooks[0]["active"] is True
