"""Integration tests for EC2 instance launch and status checks."""
# pylint: disable=missing-function-docstring
import time
import pytest


def test_instance_passes_instance_status_checks(ec2_client, test_instance):
    if not test_instance:
        pytest.fail("Test instance not created")

    max_wait_time = 600
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        response = ec2_client.describe_instance_status(InstanceIds=[test_instance])

        if response["InstanceStatuses"]:
            status = response["InstanceStatuses"][0]
            instance_status = status.get("InstanceStatus", {}).get("Status", "")

            if instance_status == "ok":
                assert instance_status == "ok"
                return

        time.sleep(15)

    pytest.fail("Instance did not pass instance status checks within timeout")
