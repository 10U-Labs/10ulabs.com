import time
import pytest


def test_console_output_is_available(ec2_client, test_instance):
    if not test_instance:
        pytest.fail("Test instance not created")

    max_attempts = 10
    console_available = False

    for _ in range(max_attempts):
        response = ec2_client.get_console_output(InstanceId=test_instance)
        output = response.get("Output", "")
        if output:
            console_available = True
            break
        time.sleep(30)

    assert console_available


def test_imdsv2_is_enforced(ec2_client, test_instance):
    if not test_instance:
        pytest.fail("Test instance not created")

    response = ec2_client.describe_instances(InstanceIds=[test_instance])
    instance = response["Reservations"][0]["Instances"][0]
    metadata_options = instance.get("MetadataOptions", {})
    http_tokens = metadata_options.get("HttpTokens", "")

    assert http_tokens == "required"
