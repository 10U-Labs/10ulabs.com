import importlib.util
import os
from pathlib import Path
from unittest.mock import MagicMock, Mock
import pytest

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_REGION'] = 'us-east-1'

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def load_module(module_name, *path_parts):
    module_path = PROJECT_ROOT / "src" / "api" / Path(*path_parts)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def v1_handler():
    return load_module("v1_handler", "lambdas", "v1.py")


@pytest.fixture
def wait_for_status_checks():
    return load_module("wait_for_status_checks", "packer", "image_for_ec2_runners_post", "wait_for_status_checks.py")


@pytest.fixture
def promote_ami():
    return load_module("promote_ami", "packer", "image_for_ec2_runners_post", "promote_ami.py")


@pytest.fixture
def mock_ec2_client():
    client = MagicMock()
    return client


@pytest.fixture
def mock_urllib_urlopen():
    from unittest.mock import patch
    with patch('urllib.request.urlopen') as mock:
        yield mock


@pytest.fixture
def mock_subprocess_run():
    from unittest.mock import patch
    with patch('subprocess.run') as mock:
        yield mock


@pytest.fixture
def mock_env_vars():
    from unittest.mock import patch
    env_vars = {
        'AWS_REGION': 'us-east-1',
        'SUBNETS': 'subnet-123,subnet-456,subnet-789',
        'VPC_ID': 'vpc-test123',
        'SECURITY_GROUPS': 'sg-12345',
        'EC2_INSTANCE_TYPES': 't4g.large,t4g.medium',
        'EC2_IAM_INSTANCE_PROFILE': 'TestInstanceProfile',
        'EC2_MAX_PRICE': '0.10',
        'GITHUB_TOKEN': 'ghp_test_token',
        'API_DOMAIN': 'api.test.com'
    }
    with patch.dict('os.environ', env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_github_token():
    from unittest.mock import patch
    with patch('os.environ.get') as mock_get:
        mock_get.return_value = 'ghp_test_token'
        yield 'ghp_test_token'
