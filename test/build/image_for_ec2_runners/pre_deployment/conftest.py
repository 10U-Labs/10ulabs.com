import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


def load_module_from_path(module_name, module_path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def cleanup_packer_artifacts():
    return load_module_from_path("cleanup_packer_artifacts", PROJECT_ROOT / "src" / "build" / "image_for_ec2_runners" / "cleanup_packer_artifacts.py")


@pytest.fixture
def packer_template_content():
    template_path = PROJECT_ROOT / "src" / "build" / "image_for_ec2_runners" / "template.pkr.hcl"
    return template_path.read_text()


@pytest.fixture
def mock_ec2(v1_handler):
    with patch('boto3.client') as mock_boto_client:
        mock_ec2_client = MagicMock()
        mock_boto_client.return_value = mock_ec2_client
        v1_handler.ec2 = mock_ec2_client
        yield mock_ec2_client


@pytest.fixture
def mock_env_vars():
    env_vars = {
        'AWS_REGION': 'us-east-1',
        'SUBNETS': 'subnet-123,subnet-456,subnet-789',
        'VPC_ID': 'vpc-test123',
        'SECURITY_GROUPS': 'sg-12345',
        'EC2_INSTANCE_TYPES': 't4g.large,t4g.medium',
        'EC2_IAM_INSTANCE_PROFILE': 'TestInstanceProfile',
        'EC2_MAX_PRICE': '0.10',
        'EC2_MANAGED_BY_TAG': 'api-ec2-spot-runner',
        'GITHUB_TOKEN': 'ghp_test_token',
        'API_DOMAIN': 'api.test.com'
    }
    with patch.dict('os.environ', env_vars, clear=False):
        yield env_vars
