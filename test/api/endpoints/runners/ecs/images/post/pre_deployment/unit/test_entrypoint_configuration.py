"""Tests for entrypoint configuration."""
import pytest


@pytest.mark.parametrize('config_args', [[
    'entrypoint.py', '--repo', 'test/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
]], indirect=True)
def test_config_sh_called_with_correct_url_format(config_args):
    """Test that config.sh is called with correct URL format."""
    assert config_args[2] == 'https://github.com/test/repo'


@pytest.mark.parametrize('config_args', [[
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'my-token'
]], indirect=True)
def test_config_sh_called_with_correct_token_parameter(config_args):
    """Test that config.sh is called with correct token parameter."""
    assert config_args[4] == 'my-token'


@pytest.mark.parametrize('config_args', [[
    'entrypoint.py', '--repo', 'org/repo', '--name', 'my-runner',
    '--labels', 'lbl', '--token', 'tok'
]], indirect=True)
def test_config_sh_called_with_correct_name_parameter(config_args):
    """Test that config.sh is called with correct name parameter."""
    assert config_args[6] == 'my-runner'


@pytest.mark.parametrize('config_args', [[
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'my-labels', '--token', 'tok'
]], indirect=True)
def test_config_sh_called_with_correct_labels_parameter(config_args):
    """Test that config.sh is called with correct labels parameter."""
    assert config_args[8] == 'my-labels'


@pytest.mark.parametrize('config_args', [[
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
]], indirect=True)
def test_config_sh_called_with_work_parameter(config_args):
    """Test that config.sh is called with work parameter."""
    assert config_args[10] == '_work'


@pytest.mark.parametrize('config_args', [[
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
]], indirect=True)
def test_config_sh_called_with_unattended_flag(config_args):
    """Test that config.sh is called with unattended flag."""
    assert config_args[11] == '--unattended'
