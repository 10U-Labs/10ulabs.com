import json
from pathlib import Path
import boto3
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parents[2] / "config" / "api.json"
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def apigw_client(config):
    return boto3.client('apigateway', region_name=config['aws_region'])


@pytest.fixture
def lambda_client(config):
    return boto3.client('lambda', region_name=config['aws_region'])


@pytest.fixture
def cloudformation_client(config):
    return boto3.client('cloudformation', region_name=config['aws_region'])


def test_api_gateway_exists(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_names = [api['name'] for api in apis['items']]
    assert 'TenULabsApi' in api_names


def test_lambda_function_exists(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    matching_functions = [name for name in function_names if 'ApiHandler' in name]
    assert len(matching_functions) > 0


def test_api_has_custom_domain_name(apigw_client, config):
    domain_names = apigw_client.get_domain_names()
    subdomain = config['subdomain_name']
    domain_name_values = [d['domainName'] for d in domain_names['items']]
    assert subdomain in domain_name_values


def test_stack_deployed_successfully(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    assert len(stacks['Stacks']) == 1


def test_stack_has_api_url_output(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    outputs = stacks['Stacks'][0].get('Outputs', [])
    output_keys = [o['OutputKey'] for o in outputs]
    assert 'ApiUrl' in output_keys


def test_stack_has_api_endpoint_output(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    outputs = stacks['Stacks'][0].get('Outputs', [])
    output_keys = [o['OutputKey'] for o in outputs]
    assert 'ApiEndpoint' in output_keys
