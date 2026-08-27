import boto3
import pytest


@pytest.fixture(scope="module")
def sqs_client(aws_region):
    return boto3.client("sqs", region_name=aws_region)


@pytest.fixture(name="api_gateway_id", scope="module")
def api_gateway_id_fixture(apigateway_client, config):
    return get_api_gateway_id_by_name(apigateway_client, config['api_gateway_name'])


@pytest.fixture(name="cloudfront_client", scope="module")
def cloudfront_client_fixture():
    return boto3.client("cloudfront")


@pytest.fixture(scope="module")
def api_distribution_id(cloudfront_client, config):
    distributions = cloudfront_client.list_distributions()
    api_fqdn = config['api_fqdn']
    dist_id = None
    for item in distributions['DistributionList']['Items']:
        aliases = item.get('Aliases', {}).get('Items', [])
        if api_fqdn in aliases:
            dist_id = item['Id']
            break
    return dist_id


@pytest.fixture(scope="module")
def first_cloudfront_dist_config(cloudfront_client):
    distributions = cloudfront_client.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        response = cloudfront_client.get_distribution_config(Id=dist_id)
        return response['DistributionConfig']
    return None


@pytest.fixture(scope="module")
def acm_client():
    return boto3.client("acm", region_name="us-east-1")


@pytest.fixture(scope="module")
def firehose_client(aws_region):
    return boto3.client("firehose", region_name=aws_region)


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


@pytest.fixture(scope="module")
def ssm_client(aws_region):
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(scope="module")
def usage_plan_id(apigateway_client, api_gateway_id):
    if api_gateway_id is None:
        return None
    usage_plans = apigateway_client.get_usage_plans()
    if not usage_plans['items']:
        return None
    return usage_plans['items'][0]['id']


@pytest.fixture(scope="module")
def api_route53_records(config):
    route53 = boto3.client('route53')
    hosted_zones = route53.list_hosted_zones_by_name(DNSName=config['domain'])
    if not hosted_zones['HostedZones']:
        return None
    zone_id = hosted_zones['HostedZones'][0]['Id']
    records = route53.list_resource_record_sets(
        HostedZoneId=zone_id,
        StartRecordName=config['api_fqdn'],
        StartRecordType='A',
        MaxItems='1'
    )
    return records['ResourceRecordSets']
