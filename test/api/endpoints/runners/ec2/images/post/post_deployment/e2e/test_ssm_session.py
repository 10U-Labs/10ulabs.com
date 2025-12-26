"""End-to-end tests for SSM Session Manager connectivity."""
import pytest


def test_ssm_session_manager_connection_works(ssm_client, e2e_test_instance, run_ssm_command):
    """Test that SSM Session Manager connection works on the EC2 instance."""
    if not e2e_test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, e2e_test_instance, "echo 'SSM Session Manager Test'")

    assert output["StandardOutputContent"].strip() == "SSM Session Manager Test"
