"""Layer 6: Capability tests.

Verify we can perform required operations on prerequisite resources.
"""
import pytest
from botocore.exceptions import ClientError

from .conftest import get_stable_ami_info

pytestmark = pytest.mark.layer(6)


def test_can_run_instances_in_subnets(ec2_client, runners_outputs):
    """Verify we can launch EC2 instances in the prerequisite subnets (dry-run)."""
    subnet_ids_str = runners_outputs.get("public_subnet_ids")
    if not subnet_ids_str:
        pytest.skip("public_subnet_ids output not found")
    subnet_ids = [s.strip() for s in subnet_ids_str.split(",") if s.strip()]
    sg_id = runners_outputs.get("security_group_id_for_runners")
    if not sg_id:
        pytest.skip("security_group_id_for_runners output not found")

    ami_info = get_stable_ami_info(ec2_client)
    if not ami_info:
        pytest.skip("No stable AMI found")
    ami_id = ami_info["id"]
    instance_type = "t4g.micro" if ami_info["arch"] == "arm64" else "t3.micro"

    try:
        ec2_client.run_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            MinCount=1,
            MaxCount=1,
            SubnetId=subnet_ids[0],
            SecurityGroupIds=[sg_id],
            DryRun=True
        )
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        assert error_code == "DryRunOperation", (
            f"No permission to launch EC2 instances in subnet {subnet_ids[0]}. "
            f"Error: {error_code}. Check IAM policy has ec2:RunInstances."
        )


def test_can_create_tags_on_instances(ec2_client):
    """Verify we have permission to describe tags (proxy for tag permissions)."""
    try:
        ec2_client.describe_tags(MaxResults=5)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        assert error_code != "AccessDenied", (
            "No permission to describe EC2 tags. "
            "Check IAM policy has ec2:DescribeTags and ec2:CreateTags."
        )
