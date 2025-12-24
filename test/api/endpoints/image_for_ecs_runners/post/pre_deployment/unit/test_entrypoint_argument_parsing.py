"""Tests for entrypoint argument parsing."""
from unittest.mock import Mock, patch
import entrypoint
import pytest


def _setup_popen_mock(mock_popen, returncode=0):
    """Configure Popen mock for argument parsing tests."""
    popen_process = Mock()
    popen_process.wait.return_value = returncode
    mock_popen.return_value.__enter__ = Mock(return_value=popen_process)
    mock_popen.return_value.__exit__ = Mock(return_value=False)
    return popen_process


def _find_config_sh_call(mock_run):
    """Find the config.sh call in the mock call list.

    The first two calls are permission-fix calls (mkdir, chown), config.sh is third.
    """
    for call in mock_run.call_args_list:
        args = call[0][0] if call[0] else []
        if args and args[0] == './config.sh':
            return args
    return None


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', '', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_parser_accepts_empty_string_for_repo(mock_run, mock_popen):
    """Test that parser accepts empty string for repo."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    config_args = _find_config_sh_call(mock_run)
    assert config_args[2] == 'https://github.com/'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', '',
    '--labels', 'lbl', '--token', 'tok'
])
def test_parser_accepts_empty_string_for_name(mock_run, mock_popen):
    """Test that parser accepts empty string for name."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    config_args = _find_config_sh_call(mock_run)
    assert config_args[6] == ''


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', '', '--token', 'tok'
])
def test_parser_accepts_empty_string_for_labels(mock_run, mock_popen):
    """Test that parser accepts empty string for labels."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    config_args = _find_config_sh_call(mock_run)
    assert config_args[8] == ''


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'my-org/my-repo-with-dashes_underscores',
    '--name', 'runner', '--labels', 'lbl', '--token', 'tok'
])
def test_parser_accepts_special_characters_in_repo(mock_run, mock_popen):
    """Test that parser accepts special characters in repo."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    config_args = _find_config_sh_call(mock_run)
    expected_url = 'https://github.com/my-org/my-repo-with-dashes_underscores'
    assert config_args[2] == expected_url


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo',
    '--name', 'runner-with-dashes_123',
    '--labels', 'lbl', '--token', 'tok'
])
def test_parser_accepts_special_characters_in_name(mock_run, mock_popen):
    """Test that parser accepts special characters in name."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    config_args = _find_config_sh_call(mock_run)
    assert config_args[6] == 'runner-with-dashes_123'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'label1,label2,label-3_test', '--token', 'tok'
])
def test_parser_accepts_comma_separated_labels(mock_run, mock_popen):
    """Test that parser accepts comma-separated labels."""
    mock_run.return_value = Mock(returncode=0)
    _setup_popen_mock(mock_popen)
    with pytest.raises(SystemExit):
        entrypoint.main()
    config_args = _find_config_sh_call(mock_run)
    assert config_args[8] == 'label1,label2,label-3_test'
