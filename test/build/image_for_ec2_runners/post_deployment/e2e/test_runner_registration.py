import time
import pytest


def test_github_runner_can_register(ssm_client, e2e_test_instance):
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
                Parameters={"commands": ["test -f /home/github-runner/actions-runner/.runner && echo 'configured' || echo 'not configured'"]}
            )

            command_id = response["Command"]["CommandId"]
            time.sleep(5)

            output = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=e2e_test_instance
            )

            if output["Status"] == "Success" and "configured" in output["StandardOutputContent"]:
                runner_configured = True
                break
        except Exception:
            pass

        time.sleep(15)

    assert runner_configured


def test_github_runner_process_is_running(ssm_client, e2e_test_instance):
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
                Parameters={"commands": ["pgrep -f 'Runner.Listener' && echo 'running' || echo 'not running'"]}
            )

            command_id = response["Command"]["CommandId"]
            time.sleep(5)

            output = ssm_client.get_command_invocation(
                CommandId=command_id,
                InstanceId=e2e_test_instance
            )

            if output["Status"] == "Success" and "running" in output["StandardOutputContent"]:
                runner_running = True
                break
        except Exception:
            pass

        time.sleep(15)

    assert runner_running
