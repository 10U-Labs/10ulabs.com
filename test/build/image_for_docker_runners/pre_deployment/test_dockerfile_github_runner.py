def test_dockerfile_installs_github_runner(dockerfile_run_commands_joined):
    assert 'actions-runner' in dockerfile_run_commands_joined


def test_dockerfile_sets_runner_version_to_2_311_0(dockerfile_runner_version):
    assert dockerfile_runner_version == '2.311.0'


def test_dockerfile_sets_runner_arch_to_arm64(dockerfile_runner_arch):
    assert dockerfile_runner_arch == 'arm64'
