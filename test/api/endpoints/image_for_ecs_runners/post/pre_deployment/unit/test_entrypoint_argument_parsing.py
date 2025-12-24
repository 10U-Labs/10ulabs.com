"""Tests for entrypoint argument parsing."""
from unittest.mock import patch
from test_helpers import run_entrypoint_and_get_config_args


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', '', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
])
def test_parser_accepts_empty_string_for_repo(mock_run, mock_popen):
    """Test that parser accepts empty string for repo."""
    config_args = run_entrypoint_and_get_config_args(mock_run, mock_popen)
    assert config_args[2] == 'https://github.com/'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', '',
    '--labels', 'lbl', '--token', 'tok'
])
def test_parser_accepts_empty_string_for_name(mock_run, mock_popen):
    """Test that parser accepts empty string for name."""
    config_args = run_entrypoint_and_get_config_args(mock_run, mock_popen)
    assert config_args[6] == ''


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', '', '--token', 'tok'
])
def test_parser_accepts_empty_string_for_labels(mock_run, mock_popen):
    """Test that parser accepts empty string for labels."""
    config_args = run_entrypoint_and_get_config_args(mock_run, mock_popen)
    assert config_args[8] == ''


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'my-org/my-repo-with-dashes_underscores',
    '--name', 'runner', '--labels', 'lbl', '--token', 'tok'
])
def test_parser_accepts_special_characters_in_repo(mock_run, mock_popen):
    """Test that parser accepts special characters in repo."""
    config_args = run_entrypoint_and_get_config_args(mock_run, mock_popen)
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
    config_args = run_entrypoint_and_get_config_args(mock_run, mock_popen)
    assert config_args[6] == 'runner-with-dashes_123'


@patch('entrypoint.subprocess.Popen')
@patch('entrypoint.subprocess.run')
@patch('sys.argv', [
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'label1,label2,label-3_test', '--token', 'tok'
])
def test_parser_accepts_comma_separated_labels(mock_run, mock_popen):
    """Test that parser accepts comma-separated labels."""
    config_args = run_entrypoint_and_get_config_args(mock_run, mock_popen)
    assert config_args[8] == 'label1,label2,label-3_test'
