"""Tests for Dockerfile AWS CLI installation."""


def test_dockerfile_installs_aws_cli(dockerfile_run_commands_joined):
    """Test that Dockerfile installs AWS CLI."""
    assert dockerfile_run_commands_joined.find('awscli') != -1


def test_dockerfile_executes_aws_cli_installer(dockerfile_run_commands_joined):
    """Test that Dockerfile executes AWS CLI installer."""
    assert dockerfile_run_commands_joined.find('/tmp/aws/install') != -1
