"""Layer 1: Existence tests for api/common/docker_repository post-deployment.

Tests ONLY that resources exist. No configuration checks.
These tests verify that resources created by THIS workflow exist after deployment.

Three-layer testing model:
- Layer 1: Existence - Resources were created
"""





class TestECRResourcesExist:
    """Layer 1: Verify ECR resources exist."""

    def test_runners_ecr_repository_exists(self, ecr_client, expected_ecr_name):
        """Verify the runners ECR repository exists."""
        response = ecr_client.describe_repositories(repositoryNames=[expected_ecr_name])
        assert len(response["repositories"]) == 1, (
            f"ECR repository '{expected_ecr_name}' not found. "
            "Run terraform apply in src/api/common/docker_repository/"
        )

    def test_runners_ecr_lifecycle_policy_exists(self, ecr_client, expected_ecr_name):
        """Verify a lifecycle policy exists for the runners ECR repository."""
        response = ecr_client.get_lifecycle_policy(repositoryName=expected_ecr_name)
        assert "lifecyclePolicyText" in response, (
            f"No lifecycle policy found for ECR repository '{expected_ecr_name}'. "
            "Run terraform apply in src/api/common/docker_repository/"
        )
