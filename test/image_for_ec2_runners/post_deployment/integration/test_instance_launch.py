import time
import pytest


def test_instance_launches_from_ami(test_instance):
    assert test_instance


def test_instance_reaches_running_state(ec2_client, test_instance):
    if not test_instance:
        pytest.fail("Test instance not created")

    waiter = ec2_client.get_waiter("instance_running")
    waiter.wait(InstanceIds=[test_instance], WaiterConfig={"Delay": 15, "MaxAttempts": 40})

    response = ec2_client.describe_instances(InstanceIds=[test_instance])
    instance_state = response["Reservations"][0]["Instances"][0]["State"]["Name"]

    assert instance_state == "running"


def test_instance_passes_system_status_checks(ec2_client, test_instance):
    if not test_instance:
        pytest.fail("Test instance not created")

    max_wait_time = 600
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        response = ec2_client.describe_instance_status(InstanceIds=[test_instance])

        if response["InstanceStatuses"]:
            status = response["InstanceStatuses"][0]
            system_status = status.get("SystemStatus", {}).get("Status", "")

            if system_status == "ok":
                assert system_status == "ok"
                return

        time.sleep(15)

    pytest.fail("Instance did not pass system status checks within timeout")


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
