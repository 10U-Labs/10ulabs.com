"""Tests for Python package installation in ECS runner image."""
from .conftest import run_command_in_container


def test_boto3_installed(docker_image):
    """Test that boto3 is installed."""
    result = run_command_in_container(docker_image, "python3 -c 'import boto3'")

    assert result.returncode == 0


def test_mypy_installed(docker_image):
    """Test that mypy is installed."""
    result = run_command_in_container(docker_image, "which mypy")

    assert result.returncode == 0


def test_pylint_installed(docker_image):
    """Test that pylint is installed."""
    result = run_command_in_container(docker_image, "which pylint")

    assert result.returncode == 0


def test_pytest_installed(docker_image):
    """Test that pytest is installed."""
    result = run_command_in_container(docker_image, "which pytest")

    assert result.returncode == 0


def test_pyyaml_installed(docker_image):
    """Test that PyYAML is installed."""
    result = run_command_in_container(docker_image, "python3 -c 'import yaml'")

    assert result.returncode == 0


def test_requests_installed(docker_image):
    """Test that requests is installed."""
    result = run_command_in_container(
        docker_image, "python3 -c 'import requests'"
    )

    assert result.returncode == 0


def test_yamllint_installed(docker_image):
    """Test that yamllint is installed."""
    result = run_command_in_container(docker_image, "which yamllint")

    assert result.returncode == 0


def test_botocore_installed(docker_image):
    """Test that botocore is installed."""
    result = run_command_in_container(
        docker_image, "python3 -c 'import botocore'"
    )

    assert result.returncode == 0


def test_boto3_stubs_installed(docker_image):
    """Test that boto3-stubs is installed."""
    result = run_command_in_container(
        docker_image,
        "python3 -c \"import importlib.metadata; "
        "importlib.metadata.version('boto3-stubs')\""
    )

    assert result.returncode == 0


def test_dnspython_installed(docker_image):
    """Test that dnspython is installed."""
    result = run_command_in_container(docker_image, "python3 -c 'import dns'")

    assert result.returncode == 0


def test_types_pyyaml_installed(docker_image):
    """Test that types-PyYAML is installed."""
    result = run_command_in_container(
        docker_image,
        "python3 -c \"import importlib.metadata; "
        "importlib.metadata.version('types-PyYAML')\""
    )

    assert result.returncode == 0


def test_types_requests_installed(docker_image):
    """Test that types-requests is installed."""
    result = run_command_in_container(
        docker_image,
        "python3 -c \"import importlib.metadata; "
        "importlib.metadata.version('types-requests')\""
    )

    assert result.returncode == 0
