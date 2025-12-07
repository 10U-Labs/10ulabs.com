"""Integration tests for source AMI availability."""
from botocore.exceptions import ClientError


class TestSourceAmiExists:
    def test_source_ami_exists_in_aws(self, ec2_client, source_ami_pattern):
        exists = False
        os_family = source_ami_pattern.get("os_family", "")
        os_version = source_ami_pattern.get("os_version", "")
        os_arch = source_ami_pattern.get("os_architecture", "arm64")
        if os_family and os_version:
            try:
                arch_filter = "arm64" if os_arch == "arm64" else "x86_64"
                response = ec2_client.describe_images(
                    Filters=[
                        {"Name": "name", "Values": [f"{os_family}-{os_version}-*"]},
                        {"Name": "architecture", "Values": [arch_filter]},
                        {"Name": "state", "Values": ["available"]},
                    ],
                    Owners=["amazon", "self", "aws-marketplace"],
                )
                exists = len(response.get("Images", [])) > 0
            except ClientError:
                exists = False
        assert exists

    def test_source_ami_is_available(self, ec2_client, source_ami_pattern):
        is_available = False
        os_family = source_ami_pattern.get("os_family", "")
        os_version = source_ami_pattern.get("os_version", "")
        os_arch = source_ami_pattern.get("os_architecture", "arm64")
        if os_family and os_version:
            try:
                arch_filter = "arm64" if os_arch == "arm64" else "x86_64"
                response = ec2_client.describe_images(
                    Filters=[
                        {"Name": "name", "Values": [f"{os_family}-{os_version}-*"]},
                        {"Name": "architecture", "Values": [arch_filter]},
                        {"Name": "state", "Values": ["available"]},
                    ],
                    Owners=["amazon", "self", "aws-marketplace"],
                )
                images = response.get("Images", [])
                if images:
                    is_available = images[0].get("State") == "available"
            except ClientError:
                is_available = False
        assert is_available
