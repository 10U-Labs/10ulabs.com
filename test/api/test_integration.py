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


@pytest.fixture
def acm_client(config):
    return boto3.client('acm', region_name=config['aws_region'])


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


def test_api_gateway_has_health_resource(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break

    resources = apigw_client.get_resources(restApiId=api_id)
    resource_paths = [r['path'] for r in resources['items']]
    assert '/health' in resource_paths


def test_api_gateway_has_v1_echo_resource(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break

    resources = apigw_client.get_resources(restApiId=api_id)
    resource_paths = [r['path'] for r in resources['items']]
    assert '/v1/echo' in resource_paths


def test_api_gateway_has_proxy_plus_resource(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break

    resources = apigw_client.get_resources(restApiId=api_id)
    resource_paths = [r['path'] for r in resources['items']]
    assert '/{proxy+}' in resource_paths


def test_api_gateway_health_has_get_method(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break

    resources = apigw_client.get_resources(restApiId=api_id)
    health_resource = None
    for r in resources['items']:
        if r['path'] == '/health':
            health_resource = r
            break

    assert 'GET' in health_resource['resourceMethods']


def test_api_gateway_echo_has_post_method(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break

    resources = apigw_client.get_resources(restApiId=api_id)
    echo_resource = None
    for r in resources['items']:
        if r['path'] == '/v1/echo':
            echo_resource = r
            break

    assert 'POST' in echo_resource['resourceMethods']


def test_certificate_exists_for_subdomain(acm_client, config):
    subdomain = config['subdomain_name']
    certificates = acm_client.list_certificates()

    cert_arns = [
        cert['CertificateArn']
        for cert in certificates['CertificateSummaryList']
        if cert['DomainName'] == subdomain
    ]
    assert len(cert_arns) > 0


def test_certificate_status_is_issued(acm_client, config):
    subdomain = config['subdomain_name']
    certificates = acm_client.list_certificates()

    cert_arn = None
    for cert in certificates['CertificateSummaryList']:
        if cert['DomainName'] == subdomain:
            cert_arn = cert['CertificateArn']
            break

    cert_details = acm_client.describe_certificate(CertificateArn=cert_arn)
    assert cert_details['Certificate']['Status'] == 'ISSUED'
