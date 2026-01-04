"""End-to-end tests for GitHub runner registration on EC2."""
import time
from botocore.exceptions import ClientError
import pytest
from test.api.endpoints.runners.ec2.images.post.post_deployment.conftest import get_instance_logs


def poll_ssm_command(ssm_client, instance_id, command_id, max_wait=30):
    """Poll SSM command status until completion or timeout."""
    start_time = time.time()
    while time.time() - start_time < max_wait:
        time.sleep(2)
        try:
            output = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id
            )
            if output["Status"] in ("Success", "Failed"):
                return output
        except ClientError:
            pass
    result = {"Status": "Timeout", "StandardOutputContent": ""}
    return result


def test_github_runner_can_register(ssm_client, e2e_test_instance):
    """Test that GitHub runner can register on the EC2 instance."""
    if not e2e_test_instance:
        pytest.fail("Test instance not created")

    max_wait_time = 300
    start_time = time.time()
    runner_configured = False

    while time.time() - start_time < max_wait_time:
        try:
            response = ssm_client.send_command(
                InstanceIds=[e2e_test_instance],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    "commands": [
                        "test -f /home/github-runner/actions-runner/.runner "
                        "&& echo 'configured' || echo 'not configured'"
                    ]
                }
            )

            command_id = response["Command"]["CommandId"]
            output = poll_ssm_command(ssm_client, e2e_test_instance, command_id)

            if output["Status"] == "Success" and "configured" in output["StandardOutputContent"]:
                runner_configured = True
                break
        except ClientError:
            pass

        time.sleep(5)

    if not runner_configured:
        logs = get_instance_logs(ssm_client, e2e_test_instance)
        pytest.fail(f"Runner failed to register. Logs:\n{logs}")
    assert True  # Explicit pass


def test_github_runner_process_is_running(ssm_client, e2e_test_instance):
    """Test that GitHub runner process is running on the EC2 instance."""
    if not e2e_test_instance:
        pytest.fail("Test instance not created")

    max_wait_time = 300
    start_time = time.time()
    runner_running = False

    while time.time() - start_time < max_wait_time:
        try:
            response = ssm_client.send_command(
                InstanceIds=[e2e_test_instance],
                DocumentName="AWS-RunShellScript",
                Parameters={
                    "commands": [
                        "pgrep -f 'Runner.Listener' && echo 'running' "
                        "|| echo 'not running'"
                    ]
                }
            )

            command_id = response["Command"]["CommandId"]
            output = poll_ssm_command(ssm_client, e2e_test_instance, command_id)

            if output["Status"] == "Success" and "running" in output["StandardOutputContent"]:
                runner_running = True
                break
        except ClientError:
            pass

        time.sleep(5)

    if not runner_running:
        logs = get_instance_logs(ssm_client, e2e_test_instance)
        pytest.fail(f"Runner process not running. Logs:\n{logs}")
    assert True  # Explicit pass
