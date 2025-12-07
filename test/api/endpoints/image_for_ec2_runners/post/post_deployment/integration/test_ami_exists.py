"""Integration tests to verify AMI exists and is available."""
import pytest


def test_ami_id_provided(test_ami_id):
    """Ami id provided."""
    assert test_ami_id


def test_ami_exists_in_ec2(ec2_client, test_ami_id):
    """Ami exists in ec2."""
    if not test_ami_id:
        pytest.fail("TEST_AMI_ID not provided")

    response = ec2_client.describe_images(ImageIds=[test_ami_id])

    assert len(response["Images"]) == 1


def test_ami_state_is_available(fetched_ami):
    """Ami state is available."""
    if not fetched_ami:
        pytest.fail("AMI details not available")

    assert fetched_ami["State"] == "available"
