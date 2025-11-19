import json
from pathlib import Path
import importlib.util
import boto3
import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Template


@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "infrastructure" / "config.json"
    with open(config_path, encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def api_stack_class():
    stack_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "infrastructure" / "stack.py"
    spec = importlib.util.spec_from_file_location("api_stack", stack_path)
    api_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(api_module)
    return api_module.ApiStack


@pytest.fixture
def cdk_app():
    return cdk.App()


@pytest.fixture
def api_stack(cdk_app, api_stack_class, config):
    return api_stack_class(
        cdk_app,
        "TestApiStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )


@pytest.fixture
def cdk_template(api_stack):
    return Template.from_stack(api_stack)


@pytest.fixture
def health_handler():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "health" / "handler.py"
    spec = importlib.util.spec_from_file_location("health_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def echo_handler():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "echo" / "handler.py"
    spec = importlib.util.spec_from_file_location("echo_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def catchall_handler():
    handler_path = Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "catchall" / "handler.py"
    spec = importlib.util.spec_from_file_location("catchall_handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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
def s3_client(config):
    return boto3.client('s3', region_name=config['aws']['region'])


@pytest.fixture
def api_id(apigw_client):
    apis = apigw_client.get_rest_apis()
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            return api['id']
    return None


@pytest.fixture
def health_function_name(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    return [name for name in function_names if 'HealthHandler' in name][0]


@pytest.fixture
def echo_function_name(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    return [name for name in function_names if 'EchoHandler' in name][0]


@pytest.fixture
def stack_outputs(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    return stacks['Stacks'][0].get('Outputs', [])


@pytest.fixture
def certificate_arn(acm_client, config):
    subdomain = config['domain_names']['subdomain']
    certificates = acm_client.list_certificates()
    for cert in certificates['CertificateSummaryList']:
        if cert['DomainName'] == subdomain:
            return cert['CertificateArn']
    return None


@pytest.fixture
def bucket_name(config):
    return config['domain_names']['subdomain']


@pytest.fixture
def api_endpoint(cloudformation_client, config):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi')
    outputs = stacks['Stacks'][0].get('Outputs', [])

    for output in outputs:
        if output['OutputKey'] == 'ApiEndpoint':
            return output['OutputValue']

    subdomain = config['domain_names']['subdomain']
    return f"https://{subdomain}"
