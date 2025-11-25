import pytest


def test_ami_architecture_matches_expected(fetched_ami, config):
    if not fetched_ami:
        pytest.fail("AMI details not available")

    expected_architecture = config["os_architecture"]

    assert fetched_ami["Architecture"] == expected_architecture


def test_ami_has_root_device_mapping(fetched_ami):
    if not fetched_ami:
        pytest.fail("AMI details not available")

    assert "BlockDeviceMappings" in fetched_ami


def test_ami_root_device_is_ebs(fetched_ami):
    if not fetched_ami:
        pytest.fail("AMI details not available")

    assert fetched_ami["RootDeviceType"] == "ebs"


def test_ami_name_follows_convention(fetched_ami):
    if not fetched_ami:
        pytest.fail("AMI details not available")

    ami_name = fetched_ami.get("Name", "")

    assert ami_name.startswith("github-ec2-runner-")


def test_ami_name_contains_architecture(fetched_ami, config):
    if not fetched_ami:
        pytest.fail("AMI details not available")

    ami_name = fetched_ami.get("Name", "")
    expected_architecture = config["os_architecture"]

    assert expected_architecture in ami_name
