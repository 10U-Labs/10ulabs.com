"""Layer 3-4: Verify a stable AMI exists for EC2 runners.

ec2_runner launches EC2 instances using AMIs created by image_for_ec2_runners.
"""


class TestStableAMI:
    """Layer 3-4: Verify a stable AMI exists and is properly configured."""

    def test_01_stable_ami_exists(self, ec2_client):
        """Layer 3: Verify at least one stable AMI exists for EC2 runners."""
        response = ec2_client.describe_images(
            Owners=["self"],
            Filters=[
                {"Name": "tag:Purpose", "Values": ["GitHub self-hosted EC2 runner"]},
                {"Name": "tag:Stable", "Values": ["true"]},
            ]
        )
        assert len(response["Images"]) >= 1, (
            "No stable AMI found with Purpose='GitHub self-hosted EC2 runner' "
            "and Stable='true'. Run the 'Building AMI for EC2 self-hosted runners' "
            "workflow to create one."
        )

    def test_02_stable_ami_is_available(self, ec2_client):
        """Layer 4: Verify the stable AMI is in available state."""
        response = ec2_client.describe_images(
            Owners=["self"],
            Filters=[
                {"Name": "tag:Purpose", "Values": ["GitHub self-hosted EC2 runner"]},
                {"Name": "tag:Stable", "Values": ["true"]},
            ]
        )
        if not response["Images"]:
            return  # Covered by existence test
        ami = response["Images"][0]
        assert ami["State"] == "available", (
            f"Stable AMI {ami['ImageId']} is in state '{ami['State']}', "
            f"not 'available'. Wait for AMI creation to complete."
        )
