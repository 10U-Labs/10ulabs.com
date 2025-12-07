"""Integration tests for AMI tags on EC2 runner image."""
import pytest


def test_ami_has_purpose_tag(ami_tags_dict):
    if not ami_tags_dict:
        pytest.fail("AMI details not available")

    assert "Purpose" in ami_tags_dict


def test_ami_purpose_tag_value(ami_purpose_tag):
    if ami_purpose_tag is None:
        pytest.fail("AMI details not available")

    assert ami_purpose_tag == "GitHub self-hosted EC2 runner"


def test_ami_has_os_family_tag(ami_tags_dict):
    if not ami_tags_dict:
        pytest.fail("AMI details not available")

    assert "OSFamily" in ami_tags_dict


def test_ami_os_family_matches_expected(ami_os_family_tag, config):
    if ami_os_family_tag is None:
        pytest.fail("AMI details not available")

    expected_os_family = config["os_family"].title()

    assert ami_os_family_tag == expected_os_family


def test_ami_has_os_version_tag(ami_tags_dict):
    if not ami_tags_dict:
        pytest.fail("AMI details not available")

    assert "OSVersion" in ami_tags_dict


def test_ami_os_version_matches_expected(ami_os_version_tag, config):
    if ami_os_version_tag is None:
        pytest.fail("AMI details not available")

    expected_os_version = config["os_version"]

    assert ami_os_version_tag == expected_os_version
