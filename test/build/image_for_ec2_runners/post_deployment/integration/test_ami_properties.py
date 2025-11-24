import pytest


def test_ami_architecture_matches_expected(ami_details, tfvars):
    if not ami_details:
        pytest.fail("AMI details not available")

    expected_architecture = tfvars["os_architecture"]

    assert ami_details["Architecture"] == expected_architecture


def test_ami_has_root_device_mapping(ami_details):
    if not ami_details:
        pytest.fail("AMI details not available")

    assert "BlockDeviceMappings" in ami_details


def test_ami_root_device_is_ebs(ami_details):
    if not ami_details:
        pytest.fail("AMI details not available")

    assert ami_details["RootDeviceType"] == "ebs"


def test_ami_name_follows_convention(ami_details):
    if not ami_details:
        pytest.fail("AMI details not available")

    ami_name = ami_details.get("Name", "")

    assert ami_name.startswith("github-ec2-runner-")


def test_ami_name_contains_architecture(ami_details, tfvars):
    if not ami_details:
        pytest.fail("AMI details not available")

    ami_name = ami_details.get("Name", "")
    expected_architecture = tfvars["os_architecture"]

    assert expected_architecture in ami_name
