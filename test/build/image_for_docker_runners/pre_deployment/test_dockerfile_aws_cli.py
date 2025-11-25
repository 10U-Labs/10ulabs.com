def test_dockerfile_installs_aws_cli(dockerfile_run_commands_joined):
    assert dockerfile_run_commands_joined.find('awscli') != -1


def test_dockerfile_executes_aws_cli_installer(dockerfile_run_commands_joined):
    assert dockerfile_run_commands_joined.find('./aws/install') != -1
