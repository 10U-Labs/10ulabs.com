"""Shared test helpers for entrypoint tests."""
from unittest.mock import Mock
import pytest
import entrypoint


def setup_popen_mock(mock_popen, returncode=0):
    """Configure Popen mock for tests.

    Args:
        mock_popen: The mock object for subprocess.Popen
        returncode: The return code for wait() (default 0)

    Returns:
        The configured mock process object
    """
    popen_process = Mock()
    popen_process.wait.return_value = returncode
    mock_popen.return_value.__enter__ = Mock(return_value=popen_process)
    mock_popen.return_value.__exit__ = Mock(return_value=False)
    return popen_process


def find_config_sh_call(mock_run):
    """Find the config.sh call in the mock call list.

    The first two calls are permission-fix calls (mkdir, chown), config.sh is third.

    Args:
        mock_run: The mock object for subprocess.run

    Returns:
        The arguments list for config.sh call, or None if not found
    """
    for call in mock_run.call_args_list:
        args = call[0][0] if call[0] else []
        if args and args[0] == './config.sh':
            return args
    return None


def run_entrypoint(mock_run, mock_popen):
    """Run the entrypoint with standard mock setup.

    Sets up mocks and runs entrypoint.main() expecting SystemExit.

    Args:
        mock_run: The mock object for subprocess.run
        mock_popen: The mock object for subprocess.Popen
    """
    mock_run.return_value = Mock(returncode=0)
    setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()


def run_entrypoint_and_get_config_args(mock_run, mock_popen):
    """Run the entrypoint and return config.sh arguments.

    Standard test helper that sets up mocks, runs entrypoint.main(),
    and extracts the config.sh call arguments.

    Args:
        mock_run: The mock object for subprocess.run
        mock_popen: The mock object for subprocess.Popen

    Returns:
        The arguments list for the config.sh call
    """
    run_entrypoint(mock_run, mock_popen)
    return find_config_sh_call(mock_run)
