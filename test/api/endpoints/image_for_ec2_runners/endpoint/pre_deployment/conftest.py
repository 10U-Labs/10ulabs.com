import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable, Generator
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
import pytest

from ..helpers import ENDPOINT_SRC, POST_DIR, get_aws_region, get_github_repo


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
LIB_PATH = str(REPO_ROOT / "lib")
if LIB_PATH not in sys.path:
    sys.path.insert(0, LIB_PATH)


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


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).parent.parent.parent.parent.parent.parent.parent


@pytest.fixture
def load_module_from_path_fixture() -> Callable[[str, Path], ModuleType]:
    def _load(name: str, path: Path) -> ModuleType:
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return _load


@pytest.fixture
def build_ami_module(project_root, load_module_from_path_fixture):
    return load_module_from_path_fixture("build_ami", POST_DIR / "build_ami.py")


@pytest.fixture
def cleanup(project_root, load_module_from_path_fixture):
    return load_module_from_path_fixture("cleanup", POST_DIR / "cleanup.py")


@pytest.fixture
def promote_ami_module(project_root, load_module_from_path_fixture):
    return load_module_from_path_fixture("promote_ami", POST_DIR / "promote_ami.py")


@pytest.fixture
def runner_config():
    return {"commands": "echo hello"}


@pytest.fixture
def provision_script_content(runner_config):
    return runner_config.get("commands", "")


@pytest.fixture
def raise_runtime_error():
    return pytest.raises(RuntimeError)


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


def _create_client_error(error_code, error_message):
    return ClientError(
        {"Error": {"Code": error_code, "Message": error_message}},
        "DescribeInstances"
    )


@pytest.fixture
def instance_not_found_error():
    return _create_client_error("InvalidInstanceID.NotFound", "The instance ID does not exist")


@pytest.fixture
def access_denied_error():
    return _create_client_error("UnauthorizedOperation", "Access denied")


def _make_ami_cleanup_params(cleanup_module, **overrides):
    params = {
        'latest_ami_id': 'ami-latest',
        'latest_snapshot_ids': set(),
        'dry_run': False,
        'cleanup_snapshots_enabled': True,
        'tags': {'Purpose': 'GitHub self-hosted EC2 runner'},
        'exclude_tags': {}
    }
    params.update(overrides)
    return cleanup_module.AmiCleanupParams(**params)


@pytest.fixture
def make_ami_cleanup_params():
    return _make_ami_cleanup_params


@pytest.fixture
def mock_ec2_client():
    return MagicMock()


@pytest.fixture
def promote_ami(promote_ami_module):
    return promote_ami_module
