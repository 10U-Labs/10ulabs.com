import pytest


def test_yq_is_installed(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "which yq")

    assert output["Status"] == "Success"


def test_yq_can_parse_yaml(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "echo 'key: value' | yq '.key'")

    assert output["StandardOutputContent"].strip() == "value"


def test_aws_cli_is_installed(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "which aws")

    assert output["Status"] == "Success"


def test_aws_cli_version_is_v2(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "aws --version")

    assert "aws-cli/2" in output["StandardOutputContent"]


def test_docker_buildx_is_available(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "docker buildx version")

    assert output["Status"] == "Success"


def test_git_is_installed(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "which git")

    assert output["Status"] == "Success"


def test_curl_is_installed(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "which curl")

    assert output["Status"] == "Success"


def test_jq_is_installed(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "which jq")

    assert output["Status"] == "Success"


def test_unzip_is_installed(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "which unzip")

    assert output["Status"] == "Success"
