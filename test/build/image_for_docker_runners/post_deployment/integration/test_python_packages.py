from conftest import run_command_in_container


def test_boto3_installed(docker_image):
    result = run_command_in_container(docker_image, "python3 -c 'import boto3'")

    assert result.returncode == 0


def test_mypy_installed(docker_image):
    result = run_command_in_container(docker_image, "which mypy")

    assert result.returncode == 0


def test_pylint_installed(docker_image):
    result = run_command_in_container(docker_image, "which pylint")

    assert result.returncode == 0


def test_pytest_installed(docker_image):
    result = run_command_in_container(docker_image, "which pytest")

    assert result.returncode == 0


def test_pyyaml_installed(docker_image):
    result = run_command_in_container(docker_image, "python3 -c 'import yaml'")

    assert result.returncode == 0


def test_requests_installed(docker_image):
    result = run_command_in_container(docker_image, "python3 -c 'import requests'")

    assert result.returncode == 0


def test_yamllint_installed(docker_image):
    result = run_command_in_container(docker_image, "which yamllint")

    assert result.returncode == 0
