"""Tests for entrypoint _diag folder permission handling.

Tests verify that the entrypoint properly sets up _diag folder permissions
before configuring the runner, enabling CloudWatch sidecar to read logs.
"""
from unittest.mock import Mock
import pytest
import entrypoint


def _find_mkdir_call(mock_run):
    """Find the mkdir call for _diag directory."""
    for call in mock_run.call_args_list:
        args = call[0][0] if call[0] else []
        if args and 'mkdir' in args and '/home/runner/_diag' in args:
            return args
    return None


def _find_chown_call(mock_run):
    """Find the chown call for _diag directory."""
    for call in mock_run.call_args_list:
        args = call[0][0] if call[0] else []
        if args and 'chown' in args and '/home/runner/_diag' in args:
            return args
    return None


def _get_call_indices(mock_run):
    """Get indices of mkdir and chown calls for _diag directory."""
    mkdir_index = None
    chown_index = None
    for i, call in enumerate(mock_run.call_args_list):
        args = call[0][0] if call[0] else []
        if args and 'mkdir' in args and '/home/runner/_diag' in args:
            mkdir_index = i
        if args and 'chown' in args and '/home/runner/_diag' in args:
            chown_index = i
    return mkdir_index, chown_index


@pytest.mark.parametrize('entrypoint_result', [[
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
]], indirect=True)
def test_main_calls_sudo_mkdir_for_diag(entrypoint_result):
    """Test that main calls sudo mkdir for _diag directory."""
    mock_run, _ = entrypoint_result
    mkdir_args = _find_mkdir_call(mock_run)
    assert mkdir_args is not None and mkdir_args[0] == 'sudo' and mkdir_args[1] == 'mkdir'


@pytest.mark.parametrize('entrypoint_result', [[
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
]], indirect=True)
def test_main_calls_sudo_chown_for_diag(entrypoint_result):
    """Test that main calls sudo chown for _diag directory."""
    mock_run, _ = entrypoint_result
    chown_args = _find_chown_call(mock_run)
    assert chown_args is not None and chown_args[0] == 'sudo' and chown_args[1] == 'chown'


@pytest.mark.parametrize('entrypoint_result', [[
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
]], indirect=True)
def test_main_calls_mkdir_before_chown(entrypoint_result):
    """Test that mkdir is called before chown for _diag directory."""
    mock_run, _ = entrypoint_result
    mkdir_index, chown_index = _get_call_indices(mock_run)
    assert mkdir_index is not None and chown_index is not None and mkdir_index < chown_index


def test_main_continues_if_permission_fix_fails(monkeypatch, entrypoint_mocks):
    """Test that main continues even if permission fix commands fail."""
    mock_run, _ = entrypoint_mocks
    mock_run.side_effect = [
        Mock(returncode=1),  # mkdir fails
        Mock(returncode=1),  # chown fails
        Mock(returncode=0),  # config.sh succeeds
    ]
    monkeypatch.setattr('sys.argv', [
        'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
        '--labels', 'lbl', '--token', 'tok'
    ])

    with pytest.raises(SystemExit) as exc_info:
        entrypoint.main()

    assert exc_info.value.code == 0
