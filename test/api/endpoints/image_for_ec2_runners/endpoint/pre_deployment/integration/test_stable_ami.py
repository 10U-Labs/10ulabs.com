"""Pre-deployment integration tests for stable AMI existence."""


def test_at_least_one_stable_ami_exists(
    ec2_client, ami_purpose_value, ami_stable_tag
):
    """Verify at least one stable AMI exists for EC2 runners."""
    response = ec2_client.describe_images(
        Owners=["self"],
        Filters=[
            {"Name": "tag:Purpose", "Values": [ami_purpose_value]},
            {"Name": f"tag:{ami_stable_tag}", "Values": ["true"]},
        ],
    )
    images = response.get("Images", [])
    assert len(images) >= 1, (
        f"No stable AMI found with Purpose={ami_purpose_value} "
        f"and {ami_stable_tag}=true"
    )


def test_stable_ami_is_available(ec2_client, ami_purpose_value, ami_stable_tag):
    """Verify that stable AMIs are in available state."""
    response = ec2_client.describe_images(
        Owners=["self"],
        Filters=[
            {"Name": "tag:Purpose", "Values": [ami_purpose_value]},
            {"Name": f"tag:{ami_stable_tag}", "Values": ["true"]},
            {"Name": "state", "Values": ["available"]},
        ],
    )
    images = response.get("Images", [])
    assert len(images) >= 1, (
        f"No available stable AMI found with Purpose={ami_purpose_value} "
        f"and {ami_stable_tag}=true"
    )
