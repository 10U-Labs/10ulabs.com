"""Post-deployment tests for naming conventions."""
import pytest
from botocore.exceptions import ClientError


class TestDeployedResourceNaming:
    """Tests to verify deployed resources follow naming conventions."""

    @pytest.fixture
    def lambda_client(self, aws_region):
        """Get Lambda client."""
        import boto3
        return boto3.client("lambda", region_name=aws_region)

    @pytest.fixture
    def ecr_client(self, aws_region):
        """Get ECR client."""
        import boto3
        return boto3.client("ecr", region_name=aws_region)

    def test_lambda_name_follows_convention(self, lambda_client, shared_config):
        """Verify Lambda function name follows naming convention."""
        resource_prefix = shared_config.get("resource_prefix", "10ulabs")

        try:
            # List functions and find agents-related ones
            paginator = lambda_client.get_paginator("list_functions")
            for page in paginator.paginate():
                for func in page.get("Functions", []):
                    name = func["FunctionName"]
                    if "agents" in name.lower() and "webhook" in name.lower():
                        # Should start with resource prefix
                        assert name.startswith(resource_prefix), (
                            f"Lambda '{name}' should start with '{resource_prefix}'"
                        )
                        return

            pytest.skip("No agents webhook Lambda found")
        except ClientError:
            pytest.skip("Could not list Lambda functions")

    def test_ecr_repository_name_follows_convention(self, ecr_client):
        """Verify ECR repository name follows naming convention."""
        try:
            response = ecr_client.describe_repositories(repositoryNames=["agents"])
            repos = response.get("repositories", [])
            if repos:
                repo_name = repos[0]["repositoryName"]
                # Should be lowercase
                assert repo_name == repo_name.lower(), (
                    f"ECR repository '{repo_name}' should be lowercase"
                )
                # Should not have underscores (ECR prefers hyphens)
                # But 'agents' is fine as single word
        except ClientError as err:
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("ECR repository 'agents' not deployed yet")
            raise
