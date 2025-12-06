"""Integration tests for SSM agent installation on EC2 runner AMI."""
# pylint: disable=missing-function-docstring
import pytest


def test_ssm_agent_is_installed(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "which amazon-ssm-agent")

    assert output["Status"] == "Success"


def test_ssm_agent_service_is_running(ssm_client, test_instance, run_ssm_command):
    if not test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, test_instance, "systemctl is-active amazon-ssm-agent")

    assert output["StandardOutputContent"].strip() == "active"
