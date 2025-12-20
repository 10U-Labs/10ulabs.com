"""Pytest fixtures for pre-deployment unit tests."""
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable, Generator
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError
import pytest
from repo_utils import REPO_ROOT

from ...helpers import ENDPOINT_SRC, POST_DIR, get_aws_region, get_github_repo


LIB_PATH = str(REPO_ROOT / "lib")
if LIB_PATH not in sys.path:
    sys.path.insert(0, LIB_PATH)


def load_handler_module() -> ModuleType:
    """Load the Lambda handler module dynamically."""
    handler_path = ENDPOINT_SRC / "lambda" / "handler.py"
    spec = importlib.util.spec_from_file_location("handler", handler_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(name="handler_module")
def _handler_module_fixture() -> Generator[ModuleType, None, None]:
    """Provide a fresh handler module with mocked environment."""
    env_vars = {
        'AWS_REGION': get_aws_region(),
        'EC2_AMI_PURPOSE_TAG': 'Purpose',
        'EC2_AMI_PURPOSE_VALUE': 'GitHub self-hosted EC2 runner',
        'EC2_AMI_STABLE_TAG': 'Stable',
        'GITHUB_REPO': get_github_repo(),
        'GITHUB_TOKEN_SECRET_NAME': '/test/github-pat',
        'SSM_EC2_RUNNER_AMI_LATEST': '/ami/ec2-runner/latest',
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
    """Provide a mock EC2 client."""
    ec2_mock = MagicMock()
    handler_module.set_client('ec2', ec2_mock)
    yield ec2_mock


@pytest.fixture(name="mock_ssm")
def _mock_ssm_fixture(handler_module: ModuleType) -> Generator[MagicMock, None, None]:
    """Provide a mock SSM client."""
    mock_ssm_client = MagicMock()
    handler_module.set_client('ssm', mock_ssm_client)
    yield mock_ssm_client


@pytest.fixture(name="mock_env_vars")
def _mock_env_vars_fixture() -> Generator[None, None, None]:
    """Provide mocked environment variables."""
    env_vars = {
        'AWS_REGION': get_aws_region(),
        'EC2_AMI_PURPOSE_TAG': 'Purpose',
        'EC2_AMI_PURPOSE_VALUE': 'GitHub self-hosted EC2 runner',
        'EC2_AMI_STABLE_TAG': 'Stable',
        'GITHUB_REPO': get_github_repo(),
        'GITHUB_TOKEN_SECRET_NAME': '/test/github-pat',
        'SSM_EC2_RUNNER_AMI_LATEST': '/ami/ec2-runner/latest',
        'SUBNETS': 'subnet-test1,subnet-test2',
        'VPC_ID': 'vpc-test',
    }
    with patch.dict('os.environ', env_vars):
        yield


@pytest.fixture
def project_root() -> Path:
    """Return the project root path."""
    return Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent


@pytest.fixture(name="module_loader")
def _module_loader_fixture() -> Callable[[str, Path], ModuleType]:
    """Provide a function to load modules from file paths."""
    def _load(name: str, path: Path) -> ModuleType:
        spec = importlib.util.spec_from_file_location(name, path)
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    return _load


@pytest.fixture(name="build_ami_module")
def _build_ami_module_fixture(module_loader):
    """Load the build_ami module."""
    return module_loader("build_ami", POST_DIR / "build_ami.py")


@pytest.fixture
def cleanup(module_loader):
    """Load the cleanup module."""
    return module_loader("cleanup", POST_DIR / "cleanup.py")


@pytest.fixture(name="promote_ami_module")
def _promote_ami_module_fixture(module_loader):
    """Load the promote_ami module."""
    return module_loader("promote_ami", POST_DIR / "promote_ami.py")


@pytest.fixture(name="runner_config")
def _runner_config_fixture():
    """Return a sample runner configuration."""
    return {"commands": "echo hello"}


@pytest.fixture
def provision_script_content(runner_config):
    """Return the provision script content from config."""
    return runner_config.get("commands", "")


@pytest.fixture
def raise_runtime_error():
    """Return a context manager for expecting RuntimeError."""
    return pytest.raises(RuntimeError)


def _create_mock_ssh_client(exit_code, encoded_output_chunks):
    """Create a mock SSH client with specified behavior."""
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
    """Return a mock SSH client that succeeds."""
    return _create_mock_ssh_client(0, [])


@pytest.fixture
def mock_ssh_client_failure():
    """Return a mock SSH client that fails with exit code 1."""
    return _create_mock_ssh_client(1, [])


@pytest.fixture
def mock_ssh_client_exit_127():
    """Return a mock SSH client that fails with exit code 127."""
    return _create_mock_ssh_client(127, [])


@pytest.fixture
def mock_ssh_client_with_output():
    """Return a mock SSH client that produces output."""
    return _create_mock_ssh_client(0, [b"hello ", b"world"])


@pytest.fixture
def mock_ssh_client_with_multiline_output():
    """Return a mock SSH client with multiline output."""
    return _create_mock_ssh_client(0, [b"line1\n", b"line2\n", b"line3\n"])


def _create_client_error(error_code, error_message):
    """Create a ClientError with specified code and message."""
    return ClientError(
        {"Error": {"Code": error_code, "Message": error_message}},
        "DescribeInstances"
    )


@pytest.fixture
def instance_not_found_error():
    """Return an instance not found ClientError."""
    return _create_client_error(
        "InvalidInstanceID.NotFound", "The instance ID does not exist"
    )


@pytest.fixture
def access_denied_error():
    """Return an access denied ClientError."""
    return _create_client_error("UnauthorizedOperation", "Access denied")


def _make_ami_cleanup_params(cleanup_module, **overrides):
    """Create AmiCleanupParams with default values and overrides."""
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
    """Return a factory function for creating AmiCleanupParams."""
    return _make_ami_cleanup_params


@pytest.fixture
def mock_ec2_client():
    """Return a mock EC2 client."""
    return MagicMock()


@pytest.fixture
def promote_ami(promote_ami_module):
    """Return the promote_ami module."""
    module = promote_ami_module
    return module


def create_mock_boto_clients():
    """Create mock EC2 and SSM clients for boto3.client patching.

    Returns a tuple of (mock_ec2, mock_ssm, side_effect_fn) where side_effect_fn
    can be used as the side_effect for a patched boto3.client.
    """
    mock_ec2 = MagicMock()
    mock_ssm = MagicMock()

    def client_side_effect(service, **_kwargs):
        return mock_ssm if service == 'ssm' else mock_ec2

    return mock_ec2, mock_ssm, client_side_effect


@pytest.fixture
def mock_boto_clients():
    """Return factory function for creating mock boto clients."""
    return create_mock_boto_clients


@pytest.fixture(name="script_file")
def _script_file_fixture(tmp_path):
    """Create a temporary script file for testing."""
    script = tmp_path / "setup.sh"
    script.write_text("#!/bin/bash\necho hello")
    return script


@pytest.fixture(name="make_script_params")
def _make_script_params_fixture(build_ami_module, script_file):
    """Factory for creating ScriptParams with sensible defaults."""
    defaults = {
        "ip_addr": "1.2.3.4",
        "key_material": "key",
        "setup_script": script_file,
        "runner_version": "1.0",
        "terraform_version": "1.0",
        "yq_version": "1.0",
        "runner_user": "test",
    }

    def _make(**kwargs):
        params = {**defaults, **kwargs}
        return build_ami_module.ScriptParams(
            params["ip_addr"],
            params["key_material"],
            params["setup_script"],
            params["runner_version"],
            params["terraform_version"],
            params["yq_version"],
            params["runner_user"],
        )
    return _make


@pytest.fixture(name="mock_ssh_context")
def _mock_ssh_context_fixture(build_ami_module):
    """Provide patched SSH client and SFTP mocks for run_script tests."""
    with patch.object(
        build_ami_module.paramiko.Ed25519Key, 'from_private_key'
    ):
        mock_client = MagicMock()
        mock_sftp = MagicMock()
        mock_client.open_sftp.return_value = mock_sftp
        with patch.object(
            build_ami_module.paramiko,
            'SSHClient',
            return_value=mock_client,
        ):
            with patch.object(build_ami_module, 'run_ssh_command'):
                yield mock_client, mock_sftp
