"""Tests for entrypoint argument parsing."""
import pytest


@pytest.mark.parametrize('config_args', [[
    'entrypoint.py', '--repo', '', '--name', 'runner',
    '--labels', 'lbl', '--token', 'tok'
]], indirect=True)
def test_parser_accepts_empty_string_for_repo(config_args):
    """Test that parser accepts empty string for repo."""
    assert config_args[2] == 'https://github.com/'


@pytest.mark.parametrize('config_args', [[
    'entrypoint.py', '--repo', 'org/repo', '--name', '',
    '--labels', 'lbl', '--token', 'tok'
]], indirect=True)
def test_parser_accepts_empty_string_for_name(config_args):
    """Test that parser accepts empty string for name."""
    assert config_args[6] == ''


@pytest.mark.parametrize('config_args', [[
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', '', '--token', 'tok'
]], indirect=True)
def test_parser_accepts_empty_string_for_labels(config_args):
    """Test that parser accepts empty string for labels."""
    assert config_args[8] == ''


@pytest.mark.parametrize('config_args', [[
    'entrypoint.py', '--repo', 'my-org/my-repo-with-dashes_underscores',
    '--name', 'runner', '--labels', 'lbl', '--token', 'tok'
]], indirect=True)
def test_parser_accepts_special_characters_in_repo(config_args):
    """Test that parser accepts special characters in repo."""
    expected_url = 'https://github.com/my-org/my-repo-with-dashes_underscores'
    assert config_args[2] == expected_url


@pytest.mark.parametrize('config_args', [[
    'entrypoint.py', '--repo', 'org/repo',
    '--name', 'runner-with-dashes_123',
    '--labels', 'lbl', '--token', 'tok'
]], indirect=True)
def test_parser_accepts_special_characters_in_name(config_args):
    """Test that parser accepts special characters in name."""
    assert config_args[6] == 'runner-with-dashes_123'


@pytest.mark.parametrize('config_args', [[
    'entrypoint.py', '--repo', 'org/repo', '--name', 'runner',
    '--labels', 'label1,label2,label-3_test', '--token', 'tok'
]], indirect=True)
def test_parser_accepts_comma_separated_labels(config_args):
    """Test that parser accepts comma-separated labels."""
    assert config_args[8] == 'label1,label2,label-3_test'
