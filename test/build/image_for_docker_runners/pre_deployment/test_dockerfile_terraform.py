def test_dockerfile_installs_terraform(dockerfile_run_commands_joined):
    assert 'terraform' in dockerfile_run_commands_joined


def test_dockerfile_sets_terraform_version_to_1_14_0(dockerfile_terraform_version):
    assert dockerfile_terraform_version == '1.14.0'


def test_dockerfile_installs_tflint(dockerfile_run_commands_joined):
    assert 'tflint' in dockerfile_run_commands_joined
