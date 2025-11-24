import os
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


@pytest.fixture(name="dynamodb_client", scope="module")
def dynamodb_client_fixture(aws_region):
    return boto3.client("dynamodb", region_name=aws_region)


@pytest.fixture(name="cloudwatch_client", scope="module")
def cloudwatch_client_fixture(aws_region):
    return boto3.client("cloudwatch", region_name=aws_region)


@pytest.fixture(name="sqs_client", scope="module")
def sqs_client_fixture(aws_region):
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(name="events_client", scope="module")
def events_client_fixture(aws_region):
    return boto3.client("events", region_name=aws_region)


@pytest.fixture(name="ec2_client", scope="module")
def ec2_client_fixture(aws_region):
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(name="github_pat", scope="module")
def github_pat_fixture():
    pat = os.environ.get("GITHUB_PAT")
    assert pat is not None
    return pat
