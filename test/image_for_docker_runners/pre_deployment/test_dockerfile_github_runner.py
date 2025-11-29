def test_dockerfile_installs_github_runner(dockerfile_run_commands_joined):
    assert dockerfile_run_commands_joined.find('actions-runner') != -1


def test_dockerfile_declares_runner_version_arg(dockerfile_content):
    assert dockerfile_content.find('ARG RUNNER_VERSION') != -1


def test_dockerfile_declares_runner_arch_arg(dockerfile_content):
    assert dockerfile_content.find('ARG RUNNER_ARCH') != -1
