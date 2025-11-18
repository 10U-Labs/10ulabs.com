import json
from pathlib import Path
import boto3
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def apigw_client(config):
    return boto3.client('apigateway', region_name=config['aws']['region'])


@pytest.fixture
def lambda_client(config):
    return boto3.client('lambda', region_name=config['aws']['region'])


@pytest.fixture
def cloudformation_client(config):
    return boto3.client('cloudformation', region_name=config['aws']['region'])


@pytest.fixture
def secretsmanager_client(config):
    return boto3.client('secretsmanager', region_name=config['aws']['region'])


@pytest.fixture
def runners_endpoint(config):
    fqdn = config['domain_names']['fqdn']
    return f"https://{fqdn}/v1/runners"
