"""Tests to validate api_shared_runners infrastructure exists.

These tests verify that the VPC infrastructure created by api_shared_runners
workflow exists and is properly configured. This is a REQUIRED prerequisite
(no defaults in data.tf) for the runners endpoint.

Five-layer testing model:
- Layer 3: Existence - Do the required resources exist?
- Layer 4: Configuration - Are resources configured correctly?
"""

import pytest
from botocore.exceptions import ClientError


class TestApiSharedRunnersOutputs:
    """Layer 3: Verify api_shared_runners terraform outputs are accessible."""

    def test_01_vpc_id_output_exists(self, api_shared_runners_outputs):
        """Verify vpc_id output exists."""
        assert api_shared_runners_outputs.get("vpc_id"), (
            "vpc_id output not found in api_shared_runners. "
            "Run: cd src/api/shared/runners && terraform apply"
        )

    def test_02_subnet_ids_output_exists(self, api_shared_runners_outputs):
        """Verify vpc_public_subnet_ids output exists."""
        assert api_shared_runners_outputs.get("vpc_public_subnet_ids"), (
            "vpc_public_subnet_ids output not found in api_shared_runners. "
            "Run: cd src/api/shared/runners && terraform apply"
        )

    def test_03_security_group_id_output_exists(self, api_shared_runners_outputs):
        """Verify runner_security_group_id output exists."""
        assert api_shared_runners_outputs.get("runner_security_group_id"), (
            "runner_security_group_id output not found in api_shared_runners. "
            "Run: cd src/api/shared/runners && terraform apply"
        )


class TestVPCResources:
    """Layer 3-4: Verify VPC resources exist and are properly configured."""

    def test_01_vpc_exists(self, ec2_client, api_shared_runners_outputs):
        """Layer 3: Verify the VPC exists."""
        vpc_id = api_shared_runners_outputs.get("vpc_id")
        if not vpc_id:
            pytest.skip("vpc_id output not available")
        try:
            response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
            assert len(response["Vpcs"]) == 1, (
                f"VPC {vpc_id} not found. "
                "Run: cd src/api/shared/runners && terraform apply"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidVpcID.NotFound":
                pytest.fail(
                    f"VPC {vpc_id} does not exist. "
                    "Run: cd src/api/shared/runners && terraform apply"
                )
            raise

    def test_02_vpc_is_available(self, ec2_client, api_shared_runners_outputs):
        """Layer 4: Verify the VPC is in available state."""
        vpc_id = api_shared_runners_outputs.get("vpc_id")
        if not vpc_id:
            pytest.skip("vpc_id output not available")
        try:
            response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
            if not response["Vpcs"]:
                pytest.skip("VPC not found - covered by existence test")
            vpc = response["Vpcs"][0]
            assert vpc["State"] == "available", (
                f"VPC {vpc_id} is in state '{vpc['State']}', not 'available'."
            )
        except ClientError:
            pytest.skip("VPC not found - covered by existence test")

    def test_03_subnets_exist(self, ec2_client, api_shared_runners_outputs):
        """Layer 3: Verify all subnets exist."""
        subnet_ids_str = api_shared_runners_outputs.get("vpc_public_subnet_ids")
        if not subnet_ids_str:
            pytest.skip("vpc_public_subnet_ids output not available")
        subnet_ids = [s.strip() for s in subnet_ids_str.split(",") if s.strip()]
        try:
            response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
            assert len(response["Subnets"]) == len(subnet_ids), (
                f"Expected {len(subnet_ids)} subnets, found {len(response['Subnets'])}. "
                "Some subnets may have been deleted."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidSubnetID.NotFound":
                pytest.fail(
                    f"One or more subnets not found: {subnet_ids}. "
                    "Run: cd src/api/shared/runners && terraform apply"
                )
            raise

    def test_04_subnets_are_available(self, ec2_client, api_shared_runners_outputs):
        """Layer 4: Verify all subnets are in available state."""
        subnet_ids_str = api_shared_runners_outputs.get("vpc_public_subnet_ids")
        if not subnet_ids_str:
            pytest.skip("vpc_public_subnet_ids output not available")
        subnet_ids = [s.strip() for s in subnet_ids_str.split(",") if s.strip()]
        try:
            response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
        except ClientError:
            pytest.skip("Subnets not found - covered by existence test")
        for subnet in response["Subnets"]:
            assert subnet["State"] == "available", (
                f"Subnet {subnet['SubnetId']} is in state '{subnet['State']}', "
                "not 'available'."
            )

    def test_05_security_group_exists(self, ec2_client, api_shared_runners_outputs):
        """Layer 3: Verify the security group exists."""
        sg_id = api_shared_runners_outputs.get("runner_security_group_id")
        if not sg_id:
            pytest.skip("runner_security_group_id output not available")
        try:
            response = ec2_client.describe_security_groups(GroupIds=[sg_id])
            assert len(response["SecurityGroups"]) == 1, (
                f"Security group {sg_id} not found."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidGroup.NotFound":
                pytest.fail(
                    f"Security group {sg_id} does not exist. "
                    "Run: cd src/api/shared/runners && terraform apply"
                )
            raise
