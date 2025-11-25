def test_dockerfile_installs_terraform(dockerfile_run_commands_joined):
    assert dockerfile_run_commands_joined.find('terraform') != -1


def test_dockerfile_declares_terraform_version_arg(dockerfile_content):
    assert dockerfile_content.find('ARG TERRAFORM_VERSION') != -1


def test_dockerfile_installs_tflint(dockerfile_run_commands_joined):
    assert dockerfile_run_commands_joined.find('tflint') != -1
