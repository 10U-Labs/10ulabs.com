import importlib.util
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


def _load_module_from_path(module_name, module_path):
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def project_root():
    return PROJECT_ROOT


@pytest.fixture
def load_module_from_path():
    return _load_module_from_path


@pytest.fixture
def build_ami_module():
    return _load_module_from_path("build_ami", PROJECT_ROOT / "src" / "build" / "image_for_ec2_runners" / "build_ami.py")


@pytest.fixture
def cleanup():
    return _load_module_from_path("cleanup", PROJECT_ROOT / "src" / "build" / "image_for_ec2_runners" / "cleanup.py")


@pytest.fixture
def provision_script_content():
    config_path = PROJECT_ROOT / "src" / "build" / "image_for_ec2_runners" / "config.yml"
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config.get("commands", "")


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


def _create_mock_ssh_client(exit_code, encoded_output_chunks):
    channel = MagicMock()
    channel.recv_exit_status.return_value = exit_code
    exit_ready_calls = [False] * len(encoded_output_chunks) + [True]
    channel.exit_status_ready.side_effect = exit_ready_calls
    recv_ready_calls = [True] * len(encoded_output_chunks) + [False]
    channel.recv_ready.side_effect = recv_ready_calls
    channel.recv.side_effect = encoded_output_chunks
    client = MagicMock()
    stdout = MagicMock()
    stdout.channel = channel
    client.exec_command.return_value = (None, stdout, None)
    return client


@pytest.fixture
def mock_ssh_client_success():
    return _create_mock_ssh_client(0, [])


@pytest.fixture
def mock_ssh_client_failure():
    return _create_mock_ssh_client(1, [])


@pytest.fixture
def mock_ssh_client_exit_127():
    return _create_mock_ssh_client(127, [])


@pytest.fixture
def mock_ssh_client_with_output():
    return _create_mock_ssh_client(0, [b"hello ", b"world"])


@pytest.fixture
def mock_ssh_client_with_multiline_output():
    return _create_mock_ssh_client(0, [b"line1\n", b"line2\n", b"line3\n"])
