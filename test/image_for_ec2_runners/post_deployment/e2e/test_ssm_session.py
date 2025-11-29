import pytest


def test_ssm_session_manager_connection_works(ssm_client, e2e_test_instance, run_ssm_command):
    if not e2e_test_instance:
        pytest.fail("Test instance not created")

    output = run_ssm_command(ssm_client, e2e_test_instance, "echo 'SSM Session Manager Test'")

    assert output["StandardOutputContent"].strip() == "SSM Session Manager Test"
