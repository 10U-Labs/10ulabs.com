import json
from pathlib import Path
import importlib.util
import boto3
import pytest
import aws_cdk as cdk
from aws_cdk.assertions import Template
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def mock_boto3_clients():
    with patch('boto3.client') as mock_client:
        mock_secretsmanager = MagicMock()
        mock_dynamodb = MagicMock()
        mock_sqs = MagicMock()
        mock_cloudwatch = MagicMock()

        def client_factory(service_name, **kwargs):
            if service_name == 'secretsmanager':
                return mock_secretsmanager
            if service_name == 'dynamodb':
                return mock_dynamodb
            if service_name == 'sqs':
                return mock_sqs
            if service_name == 'cloudwatch':
                return mock_cloudwatch
            return MagicMock()

        mock_client.side_effect = client_factory
        yield {
            'secretsmanager': mock_secretsmanager,
            'dynamodb': mock_dynamodb,
            'sqs': mock_sqs,
            'cloudwatch': mock_cloudwatch
        }


@pytest.fixture
def runners_dir():
    return Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "runners"


@pytest.fixture
def config_path(runners_dir):
    return runners_dir / "config.json"


@pytest.fixture
def stack_path(runners_dir):
    return runners_dir / "stack.py"


@pytest.fixture
def config(config_path):
    with open(config_path, encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def function_name(config):
    return config['aws']['lambda']['function_name']


@pytest.fixture
def runners_stack_class(stack_path):
    spec = importlib.util.spec_from_file_location("runners_stack", stack_path)
    runners_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runners_module)
    return runners_module.RunnersStack


@pytest.fixture
def webhook_router_path(runners_dir):
    return runners_dir / "lambda" / "webhook_router.py"


@pytest.fixture
def webhook_router_module(webhook_router_path):
    spec = importlib.util.spec_from_file_location("webhook_router", webhook_router_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def configure_webhook_handler_path(runners_dir):
    return runners_dir / "lambda" / "configure_webhook_handler.py"


@pytest.fixture
def configure_webhook_handler_module(configure_webhook_handler_path):
    spec = importlib.util.spec_from_file_location("configure_webhook_handler", configure_webhook_handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def cdk_template(runners_stack_class, config):
    app = cdk.App()
    with patch('aws_cdk.Fn.import_value') as mock_import:
        mock_import.side_effect = lambda x: f"mock-{x}"
        stack = runners_stack_class(
            app,
            "TestRunnersStack",
            config=config,
            env=cdk.Environment(
                account=str(config["aws"]["account_id"]),
                region=config["aws"]["region"]
            )
        )
        return Template.from_stack(stack)


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
    fqdn = config['fqdn']
    return f"https://{fqdn}/v1/runners"
