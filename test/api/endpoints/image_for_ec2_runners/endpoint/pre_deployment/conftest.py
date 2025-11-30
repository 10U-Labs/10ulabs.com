import importlib.util
from types import ModuleType
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from ..helpers import ENDPOINT_SRC, get_aws_region, get_github_repo


def load_handler_module() -> ModuleType:
    handler_path = ENDPOINT_SRC / "lambda" / "handler.py"
    spec = importlib.util.spec_from_file_location("handler", handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="handler_module")
def _handler_module_fixture() -> Generator[ModuleType, None, None]:
    env_vars = {
        'AWS_REGION': get_aws_region(),
        'EC2_AMI_PURPOSE_TAG': 'Purpose',
        'EC2_AMI_PURPOSE_VALUE': 'GitHub self-hosted EC2 runner',
        'EC2_AMI_STABLE_TAG': 'Stable',
        'GITHUB_REPO': get_github_repo(),
        'GITHUB_TOKEN_SECRET_NAME': '/test/github-pat',
        'SUBNETS': 'subnet-test1,subnet-test2',
        'VPC_ID': 'vpc-test',
    }
    with patch.dict('os.environ', env_vars):
        module = load_handler_module()
        if hasattr(module, '_clients'):
            setattr(module, '_clients', {})
        if hasattr(module, '_github_token_cache'):
            setattr(module, '_github_token_cache', {'value': ''})
        if hasattr(module, '_test_mode'):
            setattr(module, '_test_mode', {'enabled': False})
        yield module


@pytest.fixture(name="mock_ec2")
def _mock_ec2_fixture(handler_module: ModuleType) -> Generator[MagicMock, None, None]:
    mock_ec2_client = MagicMock()
    handler_module.set_client('ec2', mock_ec2_client)
    yield mock_ec2_client


@pytest.fixture(name="mock_ssm")
def _mock_ssm_fixture(handler_module: ModuleType) -> Generator[MagicMock, None, None]:
    mock_ssm_client = MagicMock()
    handler_module.set_client('ssm', mock_ssm_client)
    yield mock_ssm_client


@pytest.fixture(name="mock_env_vars")
def _mock_env_vars_fixture() -> Generator[None, None, None]:
    env_vars = {
        'AWS_REGION': get_aws_region(),
        'EC2_AMI_PURPOSE_TAG': 'Purpose',
        'EC2_AMI_PURPOSE_VALUE': 'GitHub self-hosted EC2 runner',
        'EC2_AMI_STABLE_TAG': 'Stable',
        'GITHUB_REPO': get_github_repo(),
        'GITHUB_TOKEN_SECRET_NAME': '/test/github-pat',
        'SUBNETS': 'subnet-test1,subnet-test2',
        'VPC_ID': 'vpc-test',
    }
    with patch.dict('os.environ', env_vars):
        yield
