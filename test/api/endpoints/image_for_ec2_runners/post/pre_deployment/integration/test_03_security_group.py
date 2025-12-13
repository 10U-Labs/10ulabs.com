"""Integration tests for security group configuration."""
import pytest
from botocore.exceptions import ClientError


class TestSecurityGroupExists:
    """Tests for security group exists."""

    def test_security_group_exists_in_aws(self, ec2_client, security_group_id):
        """Security group exists in aws."""

        if not security_group_id:
            pytest.skip("No security group ID configured")
        exists = False
        if security_group_id:
            try:
                response = ec2_client.describe_security_groups(GroupIds=[security_group_id])
                exists = len(response.get("SecurityGroups", [])) > 0
            except ClientError:
                exists = False
        assert exists

    def test_security_group_has_description(self, ec2_client, security_group_id):
        """Security group has description."""

        if not security_group_id:
            pytest.skip("No security group ID configured")
        has_description = False
        if security_group_id:
            try:
                response = ec2_client.describe_security_groups(GroupIds=[security_group_id])
                if response.get("SecurityGroups"):
                    sg = response["SecurityGroups"][0]
                    has_description = sg.get("Description", "") != ""
            except ClientError:
                has_description = False
        assert has_description

    def test_security_group_has_vpc_id(self, ec2_client, security_group_id):
        """Security group has vpc id."""

        if not security_group_id:
            pytest.skip("No security group ID configured")
        has_vpc = False
        if security_group_id:
            try:
                response = ec2_client.describe_security_groups(GroupIds=[security_group_id])
                if response.get("SecurityGroups"):
                    sg = response["SecurityGroups"][0]
                    has_vpc = sg.get("VpcId", "") != ""
            except ClientError:
                has_vpc = False
        assert has_vpc
