import boto3
import pytest

from test_fixtures.integration import get_aws_account_id_via_cli


@pytest.fixture(scope="module")
def aws_account_id():
    return get_aws_account_id_via_cli()


@pytest.fixture(scope="module")
def iam_client(config):
    return boto3.client('iam', region_name=config['aws_region'])


@pytest.fixture(scope="module", name='route53_client')
def route53_client_fixture(config):
    return boto3.client('route53', region_name=config['aws_region'])


@pytest.fixture(scope="module")
def cloudtrail_client(config):
    return boto3.client('cloudtrail', region_name=config['aws_region'])


@pytest.fixture(scope="module")
def s3_client(config):
    return boto3.client('s3', region_name=config['aws_region'])


@pytest.fixture(scope="module")
def logs_client(config):
    return boto3.client('logs', region_name=config['aws_region'])


@pytest.fixture(scope="module")
def ssm_client(config):
    return boto3.client('ssm', region_name=config['aws_region'])


@pytest.fixture(scope="module")
def hosted_zone(route53_client, config):
    zone_id = config['hosted_zone_id']
    response = route53_client.get_hosted_zone(Id=zone_id)
    return response['HostedZone']


@pytest.fixture(scope="module")
def zone_nameservers(route53_client, config):
    zone_id = config['hosted_zone_id']
    response = route53_client.get_hosted_zone(Id=zone_id)
    return response['DelegationSet']['NameServers']


@pytest.fixture(scope="module")
def ec2_client(config):
    return boto3.client('ec2', region_name=config['aws_region'])
