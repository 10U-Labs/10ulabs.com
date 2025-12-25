"""Layer 4: Existence tests.

Verify prerequisite resources exist. These are resources created by OTHER
workflows that this workflow depends on.
"""
import pytest
from botocore.exceptions import ClientError

from test_fixtures.integration import create_security_group_existence_test
from .conftest import get_stable_ami_filters

pytestmark = pytest.mark.layer(4)


class TestImageForEC2RunnersOutputs:
    """Verify image_for_ec2_runners terraform outputs exist."""

    def test_lambda_function_arn_exists(self, image_for_ec2_runners_outputs):
        """Verify lambda_function_arn output exists."""
        assert image_for_ec2_runners_outputs.get("lambda_function_arn"), (
            "lambda_function_arn output not found. "
            "Run: cd src/api/endpoints/image_for_ec2_runners && terraform apply"
        )

    def test_lambda_function_name_exists(self, image_for_ec2_runners_outputs):
        """Verify lambda_function_name output exists."""
        assert image_for_ec2_runners_outputs.get("lambda_function_name"), (
            "lambda_function_name output not found. "
            "Run: cd src/api/endpoints/image_for_ec2_runners && terraform apply"
        )

    def test_lambda_invoke_arn_exists(self, image_for_ec2_runners_outputs):
        """Verify lambda_invoke_arn output exists."""
        assert image_for_ec2_runners_outputs.get("lambda_invoke_arn"), (
            "lambda_invoke_arn output not found. "
            "Run: cd src/api/endpoints/image_for_ec2_runners && terraform apply"
        )


class TestRunnersOutputs:
    """Verify runners terraform outputs exist."""

    def test_vpc_id_output_exists(self, runners_outputs):
        """Verify vpc_id output exists."""
        assert runners_outputs.get("vpc_id"), (
            "vpc_id output not found in runners. "
            "Run: cd src/api/endpoints/webhooks/github/jit_runner_requests && terraform apply"
        )

    def test_subnet_ids_output_exists(self, runners_outputs):
        """Verify vpc_public_subnet_ids output exists."""
        assert runners_outputs.get("vpc_public_subnet_ids"), (
            "vpc_public_subnet_ids output not found in runners. "
            "Run: cd src/api/endpoints/webhooks/github/jit_runner_requests && terraform apply"
        )

    def test_security_group_id_output_exists(self, runners_outputs):
        """Verify runner_security_group_id output exists."""
        assert runners_outputs.get("runner_security_group_id"), (
            "runner_security_group_id output not found in runners. "
            "Run: cd src/api/endpoints/webhooks/github/jit_runner_requests && terraform apply"
        )


def test_stable_ami_exists(ec2_client):
    """Verify at least one stable AMI exists for EC2 runners."""
    response = ec2_client.describe_images(
        Owners=["self"],
        Filters=get_stable_ami_filters()
    )
    assert len(response["Images"]) >= 1, (
        "No stable AMI found with Purpose='GitHub self-hosted EC2 runner' "
        "and Stable='true'. Run the 'Building AMI for EC2 self-hosted runners' "
        "workflow to create one."
    )


class TestVPCResources:
    """Verify VPC resources exist."""

    def test_vpc_exists(self, ec2_client, runners_outputs):
        """Verify the VPC exists."""
        vpc_id = runners_outputs.get("vpc_id")
        if not vpc_id:
            pytest.skip("vpc_id output not found")
        try:
            response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
            assert len(response["Vpcs"]) == 1, (
                f"VPC {vpc_id} not found. "
                "Run: cd src/api/endpoints/webhooks/github/jit_runner_requests && terraform apply"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidVpcID.NotFound":
                jit_path = "src/api/endpoints/webhooks/github/jit_runner_requests"
                pytest.fail(
                    f"VPC {vpc_id} does not exist. Run: cd {jit_path} && terraform apply"
                )
            raise

    def test_subnets_exist(self, ec2_client, runners_outputs):
        """Verify all subnets exist."""
        subnet_ids_str = runners_outputs.get("vpc_public_subnet_ids")
        if not subnet_ids_str:
            pytest.skip("vpc_public_subnet_ids output not found")
        subnet_ids = [s.strip() for s in subnet_ids_str.split(",") if s.strip()]
        try:
            response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
            assert len(response["Subnets"]) == len(subnet_ids), (
                f"Expected {len(subnet_ids)} subnets, found {len(response['Subnets'])}. "
                "Some subnets may have been deleted."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "InvalidSubnetID.NotFound":
                jit_path = "src/api/endpoints/webhooks/github/jit_runner_requests"
                pytest.fail(
                    f"One or more subnets not found: {subnet_ids}. "
                    f"Run: cd {jit_path} && terraform apply"
                )
            raise

    # Use factory for security group existence test
    test_security_group_exists = create_security_group_existence_test(
        outputs_fixture="runners_outputs",
        terraform_path="src/api/endpoints/webhooks/github/jit_runner_requests",
    )
