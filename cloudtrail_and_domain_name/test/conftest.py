import json
from pathlib import Path
import boto3
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE = REPO_ROOT / 'cloudtrail_and_domain_name' / 'config.json'


def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)


@pytest.fixture
def config():
    return load_config()


@pytest.fixture
def route53_client(config):
    return boto3.client('route53', region_name=config['aws']['region'])


@pytest.fixture
def cloudtrail_client(config):
    return boto3.client('cloudtrail', region_name=config['aws']['region'])


@pytest.fixture
def s3_client(config):
    return boto3.client('s3', region_name=config['aws']['region'])


@pytest.fixture
def logs_client(config):
    return boto3.client('logs', region_name=config['aws']['region'])


@pytest.fixture
def lambda_client(config):
    return boto3.client('lambda', region_name=config['aws']['region'])


@pytest.fixture
def iam_client(config):
    return boto3.client('iam', region_name=config['aws']['region'])


@pytest.fixture
def cloudformation_client(config):
    return boto3.client('cloudformation', region_name=config['aws']['region'])


@pytest.fixture
def route53domains_client(config):
    return boto3.client('route53domains', region_name='us-east-1')


@pytest.fixture
def hosted_zone(route53_client, config):
    domain_name = config['domain_name']
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            return z
    return None


@pytest.fixture(autouse=True)
def inject_config_into_unittest_methods(request, config):
    if request.instance is not None:
        request.instance.config = config
