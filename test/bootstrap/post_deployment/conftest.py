import boto3
import pytest


@pytest.fixture
def iam_client(config):
    return boto3.client('iam', region_name=config['aws_region'])


@pytest.fixture
def route53_client(config):
    return boto3.client('route53', region_name=config['aws_region'])


@pytest.fixture
def cloudtrail_client(config):
    return boto3.client('cloudtrail', region_name=config['aws_region'])


@pytest.fixture
def s3_client(config):
    return boto3.client('s3', region_name=config['aws_region'])


@pytest.fixture
def logs_client(config):
    return boto3.client('logs', region_name=config['aws_region'])


@pytest.fixture
def ssm_client(config):
    return boto3.client('ssm', region_name=config['aws_region'])


@pytest.fixture
def hosted_zone(route53_client, config):
    zone_id = config['hosted_zone_id']
    response = route53_client.get_hosted_zone(Id=zone_id)
    return response['HostedZone']
