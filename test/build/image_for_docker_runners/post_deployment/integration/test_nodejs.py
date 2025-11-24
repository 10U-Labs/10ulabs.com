from conftest import run_command_in_container


def test_nodejs_installed(docker_image):
    result = run_command_in_container(docker_image, "which node")

    assert result.returncode == 0


def test_nodejs_version_matches(docker_image):
    result = run_command_in_container(docker_image, "node --version | grep -q 'v20.18.1'")

    assert result.returncode == 0


def test_npm_installed(docker_image):
    result = run_command_in_container(docker_image, "which npm")

    assert result.returncode == 0


def test_jsonlint_installed_globally(docker_image):
    result = run_command_in_container(docker_image, "which jsonlint")

    assert result.returncode == 0
