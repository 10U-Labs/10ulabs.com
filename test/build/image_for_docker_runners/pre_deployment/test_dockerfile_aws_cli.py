def test_dockerfile_installs_aws_cli(dockerfile_run_commands_joined):
    assert 'awscli' in dockerfile_run_commands_joined


def test_dockerfile_executes_aws_cli_installer(dockerfile_run_commands_joined):
    assert './aws/install' in dockerfile_run_commands_joined
