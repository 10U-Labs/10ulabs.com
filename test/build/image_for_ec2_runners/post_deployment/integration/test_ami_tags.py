import pytest


def test_ami_has_purpose_tag(ami_details):
    if not ami_details:
        pytest.fail("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}

    assert "Purpose" in tags


def test_ami_purpose_tag_value(ami_details):
    if not ami_details:
        pytest.fail("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}
    purpose = tags.get("Purpose", "")

    assert "GitHub" in purpose or "Github" in purpose or "github" in purpose


def test_ami_has_runner_version_tag(ami_details):
    if not ami_details:
        pytest.fail("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}

    assert "RunnerVersion" in tags


def test_ami_runner_version_matches_expected(ami_details, tfvars):
    if not ami_details:
        pytest.fail("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}
    expected_version = tfvars["github_runner_version"]
    runner_version = tags.get("RunnerVersion", "")

    assert runner_version == expected_version


def test_ami_has_os_family_tag(ami_details):
    if not ami_details:
        pytest.fail("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}

    assert "OSFamily" in tags


def test_ami_os_family_matches_expected(ami_details, tfvars):
    if not ami_details:
        pytest.fail("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}
    expected_os_family = tfvars["os_family"].title()
    os_family = tags.get("OSFamily", "")

    assert os_family == expected_os_family


def test_ami_has_os_version_tag(ami_details):
    if not ami_details:
        pytest.fail("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}

    assert "OSVersion" in tags


def test_ami_os_version_matches_expected(ami_details, tfvars):
    if not ami_details:
        pytest.fail("AMI details not available")

    tags = {tag["Key"]: tag["Value"] for tag in ami_details.get("Tags", [])}
    expected_os_version = tfvars["os_version"]
    os_version = tags.get("OSVersion", "")

    assert os_version == expected_os_version
