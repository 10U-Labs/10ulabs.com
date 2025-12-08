"""Tests to validate a stable AMI exists for EC2 runners."""


def test_stable_ami_exists(ec2_client):
    """Verify at least one stable AMI exists for EC2 runners."""
    response = ec2_client.describe_images(
        Owners=["self"],
        Filters=[
            {"Name": "tag:Purpose", "Values": ["GitHub self-hosted EC2 runner"]},
            {"Name": "tag:Stable", "Values": ["true"]},
            {"Name": "state", "Values": ["available"]}
        ]
    )
    assert len(response["Images"]) >= 1, \
        "No stable AMI found with Purpose='GitHub self-hosted EC2 runner' and Stable='true'"


def test_stable_ami_is_available(ec2_client):
    """Verify the stable AMI is in available state."""
    response = ec2_client.describe_images(
        Owners=["self"],
        Filters=[
            {"Name": "tag:Purpose", "Values": ["GitHub self-hosted EC2 runner"]},
            {"Name": "tag:Stable", "Values": ["true"]},
            {"Name": "state", "Values": ["available"]}
        ]
    )
    assert len(response["Images"]) >= 1
    ami = response["Images"][0]
    assert ami["State"] == "available", \
        f"Stable AMI {ami['ImageId']} is not in available state"
