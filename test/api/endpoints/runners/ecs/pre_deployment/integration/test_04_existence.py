"""Layer 4: Existence tests.

Verify prerequisite resources this endpoint depends on exist.
"""
from botocore.exceptions import ClientError
import pytest

pytestmark = pytest.mark.layer(4)


class TestImageForECSRunnersOutputs:
    """Verify runners/ecs/images terraform outputs are accessible."""

    def test_lambda_function_arn_output_exists(self, ecs_images_outputs):
        """Verify lambda_function_arn output is available."""
        assert ecs_images_outputs.get("lambda_function_arn"), (
            "lambda_function_arn output not found in runners/ecs/images. "
            "Run terraform apply in src/api/endpoints/runners/ecs/images/"
        )

    def test_lambda_function_name_output_exists(self, ecs_images_outputs):
        """Verify lambda_function_name output is available."""
        assert ecs_images_outputs.get("lambda_function_name"), (
            "lambda_function_name output not found in runners/ecs/images. "
            "Run terraform apply in src/api/endpoints/runners/ecs/images/"
        )

    def test_lambda_invoke_arn_output_exists(self, ecs_images_outputs):
        """Verify lambda_invoke_arn output is available."""
        assert ecs_images_outputs.get("lambda_invoke_arn"), (
            "lambda_invoke_arn output not found in runners/ecs/images. "
            "Run terraform apply in src/api/endpoints/runners/ecs/images/"
        )


class TestECRRepositoryExistence:
    """Verify ECR repository exists."""

    def test_repository_name_output_exists(self, api_shared_ecr_outputs):
        """Verify repository_name output is available."""
        assert api_shared_ecr_outputs.get("repository_name"), (
            "repository_name output not found in api_shared_ecr. "
            "Run terraform apply in src/api/shared/ecr/"
        )

    def test_ecr_repository_exists(self, ecr_client, api_shared_ecr_outputs):
        """Verify the ECR repository exists in AWS."""
        repository_name = api_shared_ecr_outputs.get("repository_name")
        if not repository_name:
            pytest.skip("repository_name output not available")
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[repository_name]
            )
            assert len(response["repositories"]) == 1, (
                f"Expected 1 repository, got {len(response['repositories'])}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.fail(
                    f"ECR repository '{repository_name}' does not exist. "
                    "Run terraform apply in src/api/shared/ecr/"
                )
            raise


class TestVPCResourcesExistence:
    """Verify VPC resources exist."""

    def test_runners_outputs_has_vpc_id(self, runners_outputs):
        """Verify vpc_id output is accessible."""
        assert runners_outputs.get("vpc_id"), "vpc_id output not found in runners"

    def test_runners_outputs_has_subnet_ids(self, runners_outputs):
        """Verify vpc_public_subnet_ids output is accessible."""
        assert runners_outputs.get("vpc_public_subnet_ids"), \
            "vpc_public_subnet_ids output not found in runners"

    def test_runners_outputs_has_security_group_id(self, runners_outputs):
        """Verify runner_security_group_id output is accessible."""
        assert runners_outputs.get("runner_security_group_id"), \
            "runner_security_group_id output not found in runners"

    def test_vpc_exists_and_available(self, ec2_client, runners_outputs):
        """Verify the VPC exists and is available."""
        vpc_id = runners_outputs.get("vpc_id")
        if not vpc_id:
            pytest.skip("vpc_id output not available")
        response = ec2_client.describe_vpcs(VpcIds=[vpc_id])
        assert response["Vpcs"][0]["State"] == "available"

    def test_subnets_exist_and_available(self, ec2_client, runners_outputs):
        """Verify all subnets exist and are available."""
        subnet_ids_str = runners_outputs.get("vpc_public_subnet_ids")
        if not subnet_ids_str:
            pytest.skip("vpc_public_subnet_ids output not available")
        subnet_ids = subnet_ids_str.split(",")
        response = ec2_client.describe_subnets(SubnetIds=subnet_ids)
        assert all(s["State"] == "available" for s in response["Subnets"])

    def test_security_group_exists(self, ec2_client, runners_outputs):
        """Verify the security group exists."""
        security_group_id = runners_outputs.get("runner_security_group_id")
        if not security_group_id:
            pytest.skip("runner_security_group_id output not available")
        response = ec2_client.describe_security_groups(GroupIds=[security_group_id])
        assert response["SecurityGroups"][0]["GroupId"] == security_group_id
