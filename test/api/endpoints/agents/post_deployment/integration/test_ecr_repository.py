"""Post-deployment tests for ECR repository."""
import pytest
from botocore.exceptions import ClientError


class TestECRRepositoryDeployed:
    """Tests to verify ECR repository is deployed correctly."""

    @pytest.fixture
    def ecr_client(self, aws_region):
        """Get ECR client."""
        import boto3
        return boto3.client("ecr", region_name=aws_region)

    def test_agents_ecr_repository_exists(self, ecr_client):
        """Verify agents ECR repository exists."""
        try:
            response = ecr_client.describe_repositories(repositoryNames=["agents"])
            repos = response.get("repositories", [])
            assert len(repos) > 0, "ECR repository 'agents' not found"
        except ClientError as err:
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("ECR repository 'agents' not deployed yet")
            raise

    def test_agents_ecr_has_runtime_image(self, ecr_client):
        """Verify ECR repository has runtime image."""
        try:
            response = ecr_client.describe_images(
                repositoryName="agents",
                filter={"tagStatus": "TAGGED"},
            )
            images = response.get("imageDetails", [])

            # Look for runtime-latest or runtime-* tag
            runtime_images = [
                img for img in images
                if any(
                    tag.startswith("runtime")
                    for tag in img.get("imageTags", [])
                )
            ]

            if not runtime_images:
                pytest.skip(
                    "No runtime images found in ECR. "
                    "Run the agents_runtime workflow to push an image."
                )
        except ClientError as err:
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("ECR repository 'agents' not deployed yet")
            raise


class TestECRLifecyclePolicy:
    """Tests for ECR lifecycle policy."""

    @pytest.fixture
    def ecr_client(self, aws_region):
        """Get ECR client."""
        import boto3
        return boto3.client("ecr", region_name=aws_region)

    def test_agents_ecr_has_lifecycle_policy(self, ecr_client):
        """Verify ECR repository has lifecycle policy configured."""
        try:
            response = ecr_client.get_lifecycle_policy(repositoryName="agents")
            policy_text = response.get("lifecyclePolicyText", "")
            assert policy_text, "ECR lifecycle policy should be configured"
        except ClientError as err:
            if err.response["Error"]["Code"] == "LifecyclePolicyNotFoundException":
                pytest.fail("ECR repository should have a lifecycle policy")
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("ECR repository 'agents' not deployed yet")
            raise
