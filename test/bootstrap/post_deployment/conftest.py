"""Pytest fixtures for bootstrap post-deployment tests."""
import boto3
import pytest


@pytest.fixture
def iam_client(config):
    """Create IAM client for AWS region."""
    return boto3.client('iam', region_name=config['aws_region'])


@pytest.fixture(name='route53_client')
def route53_client_fixture(config):
    """Create Route53 client for AWS region."""
    return boto3.client('route53', region_name=config['aws_region'])


@pytest.fixture
def cloudtrail_client(config):
    """Create CloudTrail client for AWS region."""
    return boto3.client('cloudtrail', region_name=config['aws_region'])


@pytest.fixture
def s3_client(config):
    """Create S3 client for AWS region."""
    return boto3.client('s3', region_name=config['aws_region'])


@pytest.fixture
def logs_client(config):
    """Create CloudWatch Logs client for AWS region."""
    return boto3.client('logs', region_name=config['aws_region'])


@pytest.fixture
def ssm_client(config):
    """Create SSM client for AWS region."""
    return boto3.client('ssm', region_name=config['aws_region'])


@pytest.fixture
def hosted_zone(request, config):
    """Get hosted zone details from Route53."""
    zone_id = config['hosted_zone_id']
    client = request.getfixturevalue('route53_client')
    response = client.get_hosted_zone(Id=zone_id)
    return response['HostedZone']


@pytest.fixture
def zone_nameservers(request, config):
    """Get nameservers for hosted zone."""
    zone_id = config['hosted_zone_id']
    client = request.getfixturevalue('route53_client')
    response = client.get_hosted_zone(Id=zone_id)
    return response['DelegationSet']['NameServers']
