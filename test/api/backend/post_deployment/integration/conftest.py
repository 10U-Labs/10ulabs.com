"""Pytest configuration and fixtures for post-deployment integration tests."""
import os
import boto3
import pytest


@pytest.fixture(name="lambda_client", scope="module")
def lambda_client_fixture(aws_region):
    """Create and return a boto3 Lambda client for the specified region."""
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(name="s3_client", scope="module")
def s3_client_fixture(aws_region):
    """Create and return a boto3 S3 client for the specified region."""
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(name="dynamodb_client", scope="module")
def dynamodb_client_fixture(aws_region):
    """Create and return a boto3 DynamoDB client for the specified region."""
    return boto3.client("dynamodb", region_name=aws_region)


@pytest.fixture(name="cloudwatch_client", scope="module")
def cloudwatch_client_fixture(aws_region):
    """Create and return a boto3 CloudWatch client for the specified region."""
    return boto3.client("cloudwatch", region_name=aws_region)


@pytest.fixture(name="sqs_client", scope="module")
def sqs_client_fixture(aws_region):
    """Create and return a boto3 SQS client for the specified region."""
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(name="events_client", scope="module")
def events_client_fixture(aws_region):
    """Create and return a boto3 EventBridge client for the specified region."""
    return boto3.client("events", region_name=aws_region)


@pytest.fixture(name="ec2_client", scope="module")
def ec2_client_fixture(aws_region):
    """Create and return a boto3 EC2 client for the specified region."""
    return boto3.client("ec2", region_name=aws_region)


@pytest.fixture(name="apigateway_client", scope="module")
def apigateway_client_fixture(aws_region):
    """Create and return a boto3 API Gateway client for the specified region."""
    return boto3.client("apigateway", region_name=aws_region)


@pytest.fixture(name="apigatewayv2_client", scope="module")
def apigatewayv2_client_fixture(aws_region):
    """Create and return a boto3 API Gateway V2 client for the specified region."""
    return boto3.client("apigatewayv2", region_name=aws_region)


@pytest.fixture(name="logs_client", scope="module")
def logs_client_fixture(aws_region):
    """Create and return a boto3 CloudWatch Logs client for the specified region."""
    return boto3.client("logs", region_name=aws_region)


@pytest.fixture(name="cloudfront_client", scope="module")
def cloudfront_client_fixture():
    """Create and return a boto3 CloudFront client."""
    return boto3.client("cloudfront")


@pytest.fixture(name="api_distribution_id", scope="module")
def api_distribution_id_fixture(cloudfront_client, config):
    """Find and return the CloudFront distribution ID for the API FQDN."""
    distributions = cloudfront_client.list_distributions()
    api_fqdn = config['api_fqdn']
    dist_id = None
    for item in distributions['DistributionList']['Items']:
        aliases = item.get('Aliases', {}).get('Items', [])
        if api_fqdn in aliases:
            dist_id = item['Id']
            break
    return dist_id


@pytest.fixture(name="acm_client", scope="module")
def acm_client_fixture():
    """Create and return a boto3 ACM client for us-east-1.

    CloudFront requires ACM certificates to be in us-east-1, regardless of
    where other resources are deployed.
    """
    return boto3.client("acm", region_name="us-east-1")


@pytest.fixture(name="iam_client", scope="module")
def iam_client_fixture():
    """Create and return a boto3 IAM client."""
    return boto3.client("iam")


@pytest.fixture(name="sns_client", scope="module")
def sns_client_fixture(aws_region):
    """Create and return a boto3 SNS client for the specified region."""
    return boto3.client("sns", region_name=aws_region)


@pytest.fixture(name="firehose_client", scope="module")
def firehose_client_fixture(aws_region):
    """Create and return a boto3 Firehose client for the specified region."""
    return boto3.client("firehose", region_name=aws_region)


@pytest.fixture(name="github_pat", scope="module")
def github_pat_fixture():
    """Get and return the GitHub PAT from environment variables."""
    pat = os.environ.get("GITHUB_PAT")
    assert pat is not None
    return pat


def get_api_gateway_id_by_name(client, api_name):
    """Get the API Gateway ID by searching for the API name."""
    apis = client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == api_name:
            api_id = api['id']
            break
    return api_id


def create_test_dynamodb_item(client, table_name, item):
    """Create a test item in DynamoDB table."""
    client.put_item(TableName=table_name, Item=item)


def cleanup_test_dynamodb_item(client, table_name, key):
    """Delete a test item from DynamoDB table."""
    client.delete_item(TableName=table_name, Key=key)
