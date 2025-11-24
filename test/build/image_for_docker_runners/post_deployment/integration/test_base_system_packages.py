from conftest import run_command_in_container


def test_python3_installed(docker_image):
    result = run_command_in_container(docker_image, "which python3")

    assert result.returncode == 0


def test_curl_installed(docker_image):
    result = run_command_in_container(docker_image, "which curl")

    assert result.returncode == 0


def test_git_installed(docker_image):
    result = run_command_in_container(docker_image, "which git")

    assert result.returncode == 0


def test_jq_installed(docker_image):
    result = run_command_in_container(docker_image, "which jq")

    assert result.returncode == 0


def test_sudo_installed(docker_image):
    result = run_command_in_container(docker_image, "which sudo")

    assert result.returncode == 0


def test_tar_installed(docker_image):
    result = run_command_in_container(docker_image, "which tar")

    assert result.returncode == 0


def test_unzip_installed(docker_image):
    result = run_command_in_container(docker_image, "which unzip")

    assert result.returncode == 0


def test_wget_installed(docker_image):
    result = run_command_in_container(docker_image, "which wget")

    assert result.returncode == 0
