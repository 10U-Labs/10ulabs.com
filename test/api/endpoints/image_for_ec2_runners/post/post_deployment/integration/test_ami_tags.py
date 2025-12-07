"""Integration tests for AMI tags on EC2 runner image."""
import pytest


def test_ami_has_purpose_tag(ami_tags_dict):
    """Ami has purpose tag."""

    if not ami_tags_dict:
        pytest.fail("AMI details not available")

    assert "Purpose" in ami_tags_dict


def test_ami_purpose_tag_value(ami_purpose_tag):
    """Ami purpose tag value."""

    if ami_purpose_tag is None:
        pytest.fail("AMI details not available")

    assert ami_purpose_tag == "GitHub self-hosted EC2 runner"


def test_ami_has_os_family_tag(ami_tags_dict):
    """Ami has os family tag."""

    if not ami_tags_dict:
        pytest.fail("AMI details not available")

    assert "OSFamily" in ami_tags_dict


def test_ami_os_family_matches_expected(ami_os_family_tag, config):
    """Ami os family matches expected."""

    if ami_os_family_tag is None:
        pytest.fail("AMI details not available")

    expected_os_family = config["os_family"].title()

    assert ami_os_family_tag == expected_os_family


def test_ami_has_os_version_tag(ami_tags_dict):
    """Ami has os version tag."""

    if not ami_tags_dict:
        pytest.fail("AMI details not available")

    assert "OSVersion" in ami_tags_dict


def test_ami_os_version_matches_expected(ami_os_version_tag, config):
    """Ami os version matches expected."""

    if ami_os_version_tag is None:
        pytest.fail("AMI details not available")

    expected_os_version = config["os_version"]

    assert ami_os_version_tag == expected_os_version


def test_ami_has_os_architecture_tag(ami_tags_dict):
    """Ami has os architecture tag."""

    if not ami_tags_dict:
        pytest.fail("AMI details not available")

    assert "OSArchitecture" in ami_tags_dict


def test_ami_os_architecture_matches_expected(ami_os_architecture_tag, config):
    """Ami os architecture matches expected."""

    if ami_os_architecture_tag is None:
        pytest.fail("AMI details not available")

    expected_os_architecture = config["os_architecture"]

    assert ami_os_architecture_tag == expected_os_architecture
