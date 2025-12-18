"""
Integration tests for base system packages in ECS runner image.
"""
from .conftest import run_command_in_container


def test_python3_installed(docker_image):
    """
    Test that Python 3 is installed in the container.
    """
    result = run_command_in_container(docker_image, "which python3")

    assert result.returncode == 0


def test_git_installed(docker_image):
    """
    Test that git is installed in the container.
    """
    result = run_command_in_container(docker_image, "which git")

    assert result.returncode == 0


def test_jq_installed(docker_image):
    """
    Test that jq is installed in the container.
    """
    result = run_command_in_container(docker_image, "which jq")

    assert result.returncode == 0


def test_sudo_installed(docker_image):
    """
    Test that sudo is installed in the container.
    """
    result = run_command_in_container(docker_image, "which sudo")

    assert result.returncode == 0


def test_tar_installed(docker_image):
    """
    Test that tar is installed in the container.
    """
    result = run_command_in_container(docker_image, "which tar")

    assert result.returncode == 0


def test_zip_installed(docker_image):
    """
    Test that zip is installed in the container.
    """
    result = run_command_in_container(docker_image, "which zip")

    assert result.returncode == 0


def test_python3_venv_installed(docker_image):
    """
    Test that Python venv module is installed in the container.
    """
    result = run_command_in_container(
        docker_image,
        "python3 -m venv --help"
    )

    assert result.returncode == 0


def test_procps_installed(docker_image):
    """
    Test that procps is installed in the container.
    """
    result = run_command_in_container(docker_image, "which ps")

    assert result.returncode == 0


def test_ca_certificates_installed(docker_image):
    """
    Test that CA certificates are installed in the container.
    """
    result = run_command_in_container(
        docker_image,
        "test -f /etc/ssl/certs/ca-certificates.crt"
    )

    assert result.returncode == 0


def test_libicu76_installed(docker_image):
    """
    Test that libicu76 is installed in the container.
    """
    result = run_command_in_container(
        docker_image,
        "dpkg -l | grep -q libicu76"
    )

    assert result.returncode == 0


def test_libssl3t64_installed(docker_image):
    """
    Test that libssl3t64 is installed in the container.
    """
    result = run_command_in_container(
        docker_image,
        "dpkg -l | grep -q libssl3t64"
    )

    assert result.returncode == 0


def test_liblttng_ust1_installed(docker_image):
    """
    Test that liblttng-ust1 is installed in the container.
    """
    result = run_command_in_container(
        docker_image,
        "dpkg -l | grep -q liblttng-ust1"
    )

    assert result.returncode == 0


def test_zlib1g_installed(docker_image):
    """
    Test that zlib1g is installed in the container.
    """
    result = run_command_in_container(
        docker_image,
        "dpkg -l | grep -q zlib1g"
    )

    assert result.returncode == 0
