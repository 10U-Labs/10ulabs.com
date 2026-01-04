"""Layer 2: Authorization tests.

Verify we have permission to inspect prerequisite resources.
"""
from botocore.exceptions import ClientError
import pytest

from .conftest import get_repository_name_or_skip



def _handle_ecr_client_error(error, operation, repository_name):
    """Handle ECR client errors for authorization tests."""
    if error.response["Error"]["Code"] == "AccessDeniedException":
        pytest.fail(
            f"No permission to call {operation} on '{repository_name}'. "
            "Check IAM policy."
        )
    if error.response["Error"]["Code"] == "RepositoryNotFoundException":
        pass  # Repository doesn't exist, but we have permission - OK for layer 2
    else:
        raise error


class TestECRAuthorization:
    """Test authorization to inspect ECR resources."""

    def test_can_describe_ecr_repositories(self, ecr_client, api_common_ecr_outputs):
        """Verify permission to call ecr:DescribeRepositories."""
        repository_name = get_repository_name_or_skip(api_common_ecr_outputs)
        try:
            ecr_client.describe_repositories(repositoryNames=[repository_name])
        except ClientError as e:
            _handle_ecr_client_error(e, "ecr:DescribeRepositories", repository_name)

    def test_can_list_ecr_images(self, ecr_client, api_common_ecr_outputs):
        """Verify permission to call ecr:ListImages."""
        repository_name = get_repository_name_or_skip(api_common_ecr_outputs)
        try:
            ecr_client.list_images(repositoryName=repository_name, maxResults=1)
        except ClientError as e:
            _handle_ecr_client_error(e, "ecr:ListImages", repository_name)


class TestEC2Authorization:
    """Test authorization to inspect EC2/VPC resources."""

    def test_can_describe_vpcs(self, ec2_client, runners_outputs):
        """Verify permission to call ec2:DescribeVpcs."""
        vpc_id = runners_outputs.get("vpc_id")
        if not vpc_id:
            pytest.skip("vpc_id output not available")
        try:
            ec2_client.describe_vpcs(VpcIds=[vpc_id])
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call ec2:DescribeVpcs on '{vpc_id}'. "
                    "Check IAM policy."
                )
            if e.response["Error"]["Code"] == "InvalidVpcID.NotFound":
                pass  # VPC doesn't exist, but we have permission - OK for layer 2
            else:
                raise

    def test_can_describe_subnets(self, ec2_client, runners_outputs):
        """Verify permission to call ec2:DescribeSubnets."""
        subnet_ids_str = runners_outputs.get("public_subnets_ids")
        if not subnet_ids_str:
            pytest.skip("public_subnets_ids output not available")
        subnet_ids = subnet_ids_str.split(",")
        try:
            ec2_client.describe_subnets(SubnetIds=subnet_ids)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ec2:DescribeSubnets. Check IAM policy."
                )
            if e.response["Error"]["Code"] == "InvalidSubnetID.NotFound":
                pass  # Subnets don't exist, but we have permission - OK for layer 2
            else:
                raise

    def test_can_describe_security_groups(self, ec2_client, runners_outputs):
        """Verify permission to call ec2:DescribeSecurityGroups."""
        sg_id = runners_outputs.get("security_group_id_for_runners")
        if not sg_id:
            pytest.skip("security_group_id_for_runners output not available")
        try:
            ec2_client.describe_security_groups(GroupIds=[sg_id])
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    f"No permission to call ec2:DescribeSecurityGroups on '{sg_id}'. "
                    "Check IAM policy."
                )
            if e.response["Error"]["Code"] == "InvalidGroup.NotFound":
                pass  # SG doesn't exist, but we have permission - OK for layer 2
            else:
                raise
