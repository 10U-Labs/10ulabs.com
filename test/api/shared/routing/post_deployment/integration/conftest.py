"""Pytest configuration and fixtures for post-deployment integration tests."""
import boto3
import pytest

# Note: The following fixtures are inherited from parent conftest files:
# - From test_fixtures/aws.py: iam_client, s3_client, logs_client, apigateway_client,
#   ec2_client, lambda_client, dynamodb_client
# - From routing/conftest.py: cloudwatch_client, events_client, sns_client


@pytest.fixture(name="sqs_client", scope="module")
def sqs_client_fixture(aws_region):
    """Create and return a boto3 SQS client for the specified region."""
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(name="api_gateway_id", scope="module")
def api_gateway_id_fixture(apigateway_client, config):
    """Get API Gateway REST API ID by name."""
    return get_api_gateway_id_by_name(apigateway_client, config['api_gateway_name'])


@pytest.fixture(name="apigatewayv2_client", scope="module")
def apigatewayv2_client_fixture(aws_region):
    """Create and return a boto3 API Gateway V2 client for the specified region."""
    return boto3.client("apigatewayv2", region_name=aws_region)


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


@pytest.fixture(name="first_cloudfront_dist_config", scope="module")
def first_cloudfront_dist_config_fixture(cloudfront_client):
    """Get the DistributionConfig of the first CloudFront distribution."""
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        response = cloudfront_client.get_distribution_config(Id=dist_id)
        return response['DistributionConfig']
    return None


@pytest.fixture(name="acm_client", scope="module")
def acm_client_fixture():
    """Create and return a boto3 ACM client for us-east-1.

    CloudFront requires ACM certificates to be in us-east-1, regardless of
    where other resources are deployed.
    """
    return boto3.client("acm", region_name="us-east-1")


@pytest.fixture(name="firehose_client", scope="module")
def firehose_client_fixture(aws_region):
    """Create and return a boto3 Firehose client for the specified region."""
    return boto3.client("firehose", region_name=aws_region)


@pytest.fixture(name="waf_logging_config", scope="module")
def waf_logging_config_fixture():
    """Get WAF logging configuration for the first CloudFront Web ACL."""
    waf_client = boto3.client('wafv2', region_name='us-east-1')
    response = waf_client.list_web_acls(Scope='CLOUDFRONT')
    if response['WebACLs']:
        acl = response['WebACLs'][0]
        acl_arn = acl['ARN']
        logging_response = waf_client.get_logging_configuration(ResourceArn=acl_arn)
        return logging_response.get('LoggingConfiguration')
    return None


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
