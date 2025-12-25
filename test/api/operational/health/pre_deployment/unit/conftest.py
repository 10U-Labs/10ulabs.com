"""Pytest fixtures for health endpoint pre-deployment tests."""
from types import ModuleType
from typing import Dict
from unittest.mock import MagicMock, patch

from test.api.operational.health.conftest import HEALTH_SRC

import pytest
from botocore.exceptions import ClientError

from boto_mocks import setup_mock_ec2_vpc_responses
from module_utils import create_lambda_loader


def load_health_handler_module() -> ModuleType:
    """Load the health handler module dynamically."""
    loader = create_lambda_loader(HEALTH_SRC / "lambda")
    return loader("handler.py", "health_handler")


@pytest.fixture
def health_handler() -> ModuleType:
    """Create health handler module fixture."""
    return load_health_handler_module()


@pytest.fixture
def health_get_event():
    """Create GET /health event fixture."""
    return {'path': '/health', 'httpMethod': 'GET'}


@pytest.fixture
def health_dependencies_get_event():
    """Create GET /health/dependencies event fixture."""
    return {'path': '/health/dependencies', 'httpMethod': 'GET'}


@pytest.fixture
def valid_dependency_env_vars() -> Dict[str, str]:
    """Create standard environment variables for dependency validation tests."""
    return {
        'SECURITY_GROUPS': 'sg-test',
        'SUBNETS': 'subnet-test1,subnet-test2',
        'VPC_ID': 'vpc-test'
    }


@pytest.fixture
def mock_ec2_valid_deps() -> MagicMock:
    """Create mock EC2 client with all valid dependencies."""
    mock_ec2 = MagicMock()
    setup_mock_ec2_vpc_responses(mock_ec2)
    return mock_ec2


@pytest.fixture
def mock_ec2_missing_sg() -> MagicMock:
    """Create mock EC2 client with missing security group."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_security_groups.side_effect = ClientError(
        {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
        'DescribeSecurityGroups'
    )
    mock_ec2.describe_subnets.return_value = {
        'Subnets': [{'SubnetId': 'subnet-test1'}, {'SubnetId': 'subnet-test2'}]
    }
    mock_ec2.describe_vpcs.return_value = {'Vpcs': [{'VpcId': 'vpc-test'}]}
    return mock_ec2


@pytest.fixture
def patched_dependency_env(request):
    """Fixture that patches environment with dependency env vars."""
    env_vars = request.getfixturevalue('valid_dependency_env_vars')
    with patch.dict('os.environ', env_vars):
        yield


@pytest.fixture
def mock_ec2_sg_not_found() -> MagicMock:
    """Create mock EC2 client that returns security group not found error."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_security_groups.side_effect = ClientError(
        {'Error': {'Code': 'InvalidGroup.NotFound', 'Message': 'Not found'}},
        'DescribeSecurityGroups'
    )
    return mock_ec2


@pytest.fixture
def mock_ec2_subnet_not_found() -> MagicMock:
    """Create mock EC2 client that returns subnet not found error."""
    mock_ec2 = MagicMock()
    mock_ec2.describe_subnets.side_effect = ClientError(
        {'Error': {'Code': 'InvalidSubnetID.NotFound', 'Message': 'Not found'}},
        'DescribeSubnets'
    )
    return mock_ec2
