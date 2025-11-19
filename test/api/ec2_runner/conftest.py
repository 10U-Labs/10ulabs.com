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
        mock_ec2 = MagicMock()
        mock_secretsmanager = MagicMock()

        def client_factory(service_name, **kwargs):
            if service_name == 'ec2':
                return mock_ec2
            if service_name == 'secretsmanager':
                return mock_secretsmanager
            return MagicMock()

        mock_client.side_effect = client_factory
        yield {
            'ec2': mock_ec2,
            'secretsmanager': mock_secretsmanager
        }


@pytest.fixture
def endpoint_dir():
    return Path(__file__).parent.parent.parent.parent / "src" / "api" / "endpoints" / "v1" / "ec2_runner"


@pytest.fixture
def config_path(endpoint_dir):
    return endpoint_dir / "config.json"


@pytest.fixture
def config(config_path):
    with open(config_path, encoding='utf-8') as f:
        return json.load(f)


@pytest.fixture
def stack_path(endpoint_dir):
    return endpoint_dir / "stack.py"


@pytest.fixture
def handler_path(endpoint_dir):
    return endpoint_dir / "handler.py"


@pytest.fixture
def stack_class(stack_path):
    spec = importlib.util.spec_from_file_location("ec2_runner_stack", stack_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.EC2RunnerStack


@pytest.fixture
def handler_module(handler_path):
    spec = importlib.util.spec_from_file_location("handler", handler_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def cdk_template(stack_class, config):
    app = cdk.App()
    with patch('aws_cdk.Fn.import_value') as mock_import:
        mock_import.side_effect = lambda x: f"mock-{x}"
        stack = stack_class(
            app,
            "TestEC2RunnerStack",
            config=config,
            env=cdk.Environment(
                account=str(config["aws"]["account_id"]),
                region=config["aws"]["region"]
            )
        )
        return Template.from_stack(stack)


@pytest.fixture
def ec2_client(config):
    return boto3.client('ec2', region_name=config['aws']['region'])


@pytest.fixture
def lambda_client(config):
    return boto3.client('lambda', region_name=config['aws']['region'])


@pytest.fixture
def endpoint_url(config):
    return f"https://{config['domain_names']['subdomain']}/v1/ec2-runner"
