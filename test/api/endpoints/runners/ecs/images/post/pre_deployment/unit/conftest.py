"""Fixtures for pre-deployment tests of ECS runner Docker image."""
import importlib.util
import os
import sys
from test.api.endpoints.runners.ecs.images.conftest import (
    BASE_DIR,
    FILES_DIR,
)
from unittest.mock import Mock

import pytest

# Add directories to path for imports
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, FILES_DIR)
entrypoint_path = os.path.join(FILES_DIR, 'entrypoint.py')
entrypoint_spec = importlib.util.spec_from_file_location("entrypoint", entrypoint_path)
if entrypoint_spec is None or entrypoint_spec.loader is None:
    raise ImportError("Could not load entrypoint module")
_entrypoint_module = importlib.util.module_from_spec(entrypoint_spec)
sys.modules['entrypoint'] = _entrypoint_module
entrypoint_spec.loader.exec_module(_entrypoint_module)


@pytest.fixture
def entrypoint():
    """Provide access to the entrypoint module."""
    return _entrypoint_module


@pytest.fixture(autouse=True)
def reset_monitor_state():
    """Reset entrypoint monitor_state before each test to ensure test isolation."""
    _entrypoint_module.monitor_state["should_terminate"] = False
    _entrypoint_module.monitor_state["stop_event"] = None
    yield


promote_path = os.path.join(FILES_DIR, 'promote_docker_image.py')
promote_spec = importlib.util.spec_from_file_location("promote_docker_image", promote_path)
if promote_spec is None or promote_spec.loader is None:
    raise ImportError("Could not load promote_docker_image module")
promote_docker_image = importlib.util.module_from_spec(promote_spec)
sys.modules['promote_docker_image'] = promote_docker_image
promote_spec.loader.exec_module(promote_docker_image)


# --- Entrypoint test fixtures ---


@pytest.fixture
def entrypoint_mocks(monkeypatch):
    """Patch subprocess for entrypoint tests.

    Returns (mock_run, mock_popen) tuple for tests that need to inspect calls.
    """
    mock_run = Mock(return_value=Mock(returncode=0))
    mock_popen = Mock()
    popen_process = Mock()
    popen_process.wait.return_value = 0
    mock_popen.return_value.__enter__ = Mock(return_value=popen_process)
    mock_popen.return_value.__exit__ = Mock(return_value=False)

    monkeypatch.setattr('entrypoint.subprocess.run', mock_run)
    monkeypatch.setattr('entrypoint.subprocess.Popen', mock_popen)
    return mock_run, mock_popen


@pytest.fixture
def entrypoint_result(request, monkeypatch, entrypoint_mocks):
    """Run entrypoint.main() with given argv and return mocks.

    Use with @pytest.mark.parametrize('entrypoint_result', [argv], indirect=True)
    """
    argv = request.param
    monkeypatch.setattr('sys.argv', argv)
    with pytest.raises(SystemExit):
        _entrypoint_module.main()
    return entrypoint_mocks


@pytest.fixture
def config_args(request, monkeypatch, entrypoint_mocks):
    """Run entrypoint with given argv and return config.sh arguments.

    Use with @pytest.mark.parametrize('config_args', [argv], indirect=True)
    """
    argv = request.param
    monkeypatch.setattr('sys.argv', argv)
    with pytest.raises(SystemExit):
        _entrypoint_module.main()

    mock_run, _ = entrypoint_mocks
    for call in mock_run.call_args_list:
        args = call[0][0] if call[0] else []
        if args and args[0] == './config.sh':
            return args
    return None
