import json
from pathlib import Path
import boto3
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent.parent / "src" / "api" / "self" / "config.json"
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
def acm_client(config):
    return boto3.client('acm', region_name=config['aws']['region'])


@pytest.fixture
def api_endpoint(cloudformation_client, config):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    outputs = stacks['Stacks'][0].get('Outputs', [])

    for output in outputs:
        if output['OutputKey'] == 'ApiEndpoint':
            return output['OutputValue']

    subdomain = config['domain_names']['subdomain']
    return f"https://{subdomain}"
