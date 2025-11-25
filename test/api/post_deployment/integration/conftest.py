import os
import boto3
import pytest


@pytest.fixture(name="lambda_client", scope="module")
def lambda_client_fixture(aws_region):
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(name="s3_client", scope="module")
def s3_client_fixture(aws_region):
    return boto3.client("s3", region_name=aws_region)


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


@pytest.fixture(name="apigateway_client", scope="module")
def apigateway_client_fixture(aws_region):
    return boto3.client("apigateway", region_name=aws_region)


@pytest.fixture(name="apigatewayv2_client", scope="module")
def apigatewayv2_client_fixture(aws_region):
    return boto3.client("apigatewayv2", region_name=aws_region)


@pytest.fixture(name="logs_client", scope="module")
def logs_client_fixture(aws_region):
    return boto3.client("logs", region_name=aws_region)


@pytest.fixture(name="cloudfront_client", scope="module")
def cloudfront_client_fixture():
    return boto3.client("cloudfront")


@pytest.fixture(name="acm_client", scope="module")
def acm_client_fixture(aws_region):
    return boto3.client("acm", region_name=aws_region)


@pytest.fixture(name="iam_client", scope="module")
def iam_client_fixture():
    return boto3.client("iam")


@pytest.fixture(name="sns_client", scope="module")
def sns_client_fixture(aws_region):
    return boto3.client("sns", region_name=aws_region)


@pytest.fixture(name="firehose_client", scope="module")
def firehose_client_fixture(aws_region):
    return boto3.client("firehose", region_name=aws_region)


@pytest.fixture(name="github_pat", scope="module")
def github_pat_fixture():
    pat = os.environ.get("GITHUB_PAT")
    assert pat is not None
    return pat


def get_api_gateway_id_by_name(client, api_name):
    apis = client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == api_name:
            api_id = api['id']
            break
    return api_id


def create_test_dynamodb_item(client, table_name, item):
    client.put_item(TableName=table_name, Item=item)


def cleanup_test_dynamodb_item(client, table_name, key):
    client.delete_item(TableName=table_name, Key=key)
