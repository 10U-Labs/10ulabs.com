"""Integration tests for pip packages on EC2 runner AMI."""
import pytest


def test_boto3_is_importable(ssm_client, test_instance, run_ssm_command):
    """Boto3 is importable."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -c 'import boto3'")

    assert output["Status"] == "Success"


def test_boto3_stubs_is_installed(ssm_client, test_instance, run_ssm_command):
    """Boto3 stubs is installed."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -m pip show boto3-stubs")

    assert output["Status"] == "Success"


def test_botocore_is_importable(ssm_client, test_instance, run_ssm_command):
    """Botocore is importable."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -c 'import botocore'")

    assert output["Status"] == "Success"


def test_dnspython_is_importable(ssm_client, test_instance, run_ssm_command):
    """Dnspython is importable."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -c 'import dns'")

    assert output["Status"] == "Success"


def test_dockerfile_parse_is_importable(ssm_client, test_instance, run_ssm_command):
    """Dockerfile parse is importable."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -c 'import dockerfile_parse'")

    assert output["Status"] == "Success"


def test_mypy_is_importable(ssm_client, test_instance, run_ssm_command):
    """Mypy is importable."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -c 'import mypy'")

    assert output["Status"] == "Success"


def test_mypy_can_run_version_check(ssm_client, test_instance, run_ssm_command):
    """Mypy can run version check."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -m mypy --version")

    assert output["Status"] == "Success"


def test_pylint_is_importable(ssm_client, test_instance, run_ssm_command):
    """Pylint is importable."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -c 'import pylint'")

    assert output["Status"] == "Success"


def test_pylint_can_run_version_check(ssm_client, test_instance, run_ssm_command):
    """Pylint can run version check."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -m pylint --version")

    assert output["Status"] == "Success"


def test_python_hcl2_is_importable(ssm_client, test_instance, run_ssm_command):
    """Python hcl2 is importable."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -c 'import hcl2'")

    assert output["Status"] == "Success"


def test_pyyaml_is_importable(ssm_client, test_instance, run_ssm_command):
    """Pyyaml is importable."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -c 'import yaml'")

    assert output["Status"] == "Success"


def test_requests_is_importable(ssm_client, test_instance, run_ssm_command):
    """Requests is importable."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -c 'import requests'")

    assert output["Status"] == "Success"


def test_types_pyyaml_is_installed(ssm_client, test_instance, run_ssm_command):
    """Types pyyaml is installed."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -m pip show types-PyYAML")

    assert output["Status"] == "Success"


def test_types_dockerfile_parse_is_installed(ssm_client, test_instance, run_ssm_command):
    """Types dockerfile parse is installed."""

    if not test_instance:
        pytest.fail("Test instance not created")

    cmd = "python3 -m pip show types-dockerfile-parse"
    output = run_ssm_command(ssm_client, test_instance, cmd)

    assert output["Status"] == "Success"


def test_types_requests_is_installed(ssm_client, test_instance, run_ssm_command):
    """Types requests is installed."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -m pip show types-requests")

    assert output["Status"] == "Success"


def test_yamllint_is_importable(ssm_client, test_instance, run_ssm_command):
    """Yamllint is importable."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -c 'import yamllint'")

    assert output["Status"] == "Success"


def test_yamllint_can_run_version_check(ssm_client, test_instance, run_ssm_command):
    """Yamllint can run version check."""

    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "python3 -m yamllint --version")

    assert output["Status"] == "Success"
