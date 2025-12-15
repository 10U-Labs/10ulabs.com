"""Tests to validate agents_shared prerequisites before troubleshooter_of_workflows deployment.

This endpoint depends on resources created by the agents_shared workflow:
- ECR repository for agent container images
- Lambda layer for GitHub authentication

Five-layer testing model:
- Layer 1: Authentication - Covered by test_01_iam_role.py
- Layer 2: Authorization - Can we call ECR and Lambda APIs?
- Layer 3: Existence - Do the prerequisite resources exist?
- Layer 4: Configuration - Are they configured correctly?
- Layer 5: Capability - Can we perform required operations?
"""

from botocore.exceptions import ClientError
import pytest


class TestECRAPIAuthorization:
    """Layer 2: Verify we can call ECR APIs."""

    def test_01_can_call_describe_repositories_api(self, ecr_client):
        """Verify we have permission to call ecr:DescribeRepositories."""
        try:
            ecr_client.describe_repositories(maxResults=1)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ecr:DescribeRepositories. "
                    "Check IAM permissions for ecr:DescribeRepositories."
                )
            raise

    def test_02_can_call_list_images_api(self, ecr_client, agents_shared_outputs):
        """Verify we have permission to call ecr:ListImages."""
        repository_name = agents_shared_outputs.get("ecr_repository_name")
        if not repository_name:
            pytest.skip("ecr_repository_name output not available")
        try:
            ecr_client.list_images(repositoryName=repository_name, maxResults=1)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call ecr:ListImages. "
                    "Check IAM permissions for ecr:ListImages."
                )
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pass  # Existence check is in Layer 3
            else:
                raise


class TestLambdaAPIAuthorization:
    """Layer 2: Verify we can call Lambda APIs."""

    def test_01_can_call_list_layers_api(self, lambda_client):
        """Verify we have permission to call lambda:ListLayers."""
        try:
            lambda_client.list_layers(MaxItems=1)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call lambda:ListLayers. "
                    "Check IAM permissions for lambda:ListLayers."
                )
            raise

    def test_02_can_call_get_layer_version_api(self, lambda_client, agents_shared_outputs):
        """Verify we have permission to call lambda:GetLayerVersionByArn."""
        layer_arn = agents_shared_outputs.get("lambda_layer_github_auth_arn")
        if not layer_arn:
            pytest.skip("lambda_layer_github_auth_arn output not available")
        try:
            lambda_client.get_layer_version_by_arn(Arn=layer_arn)
        except ClientError as err:
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    "No permission to call lambda:GetLayerVersionByArn. "
                    "Check IAM permissions for lambda:GetLayerVersion."
                )
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pass  # Existence check is in Layer 3
            else:
                raise


class TestAgentsSharedOutputsExistence:
    """Layer 3: Verify agents_shared terraform outputs are available."""

    def test_01_ecr_repository_arn_output_exists(self, agents_shared_outputs):
        """Verify ecr_repository_arn output is available."""
        assert agents_shared_outputs.get("ecr_repository_arn"), (
            "ecr_repository_arn output not found in agents_shared. "
            "Run terraform apply in src/api/endpoints/agents/shared/"
        )

    def test_02_ecr_repository_name_output_exists(self, agents_shared_outputs):
        """Verify ecr_repository_name output is available."""
        assert agents_shared_outputs.get("ecr_repository_name"), (
            "ecr_repository_name output not found in agents_shared. "
            "Run terraform apply in src/api/endpoints/agents/shared/"
        )

    def test_03_ecr_repository_url_output_exists(self, agents_shared_outputs):
        """Verify ecr_repository_url output is available."""
        assert agents_shared_outputs.get("ecr_repository_url"), (
            "ecr_repository_url output not found in agents_shared. "
            "Run terraform apply in src/api/endpoints/agents/shared/"
        )

    def test_04_lambda_layer_github_auth_arn_output_exists(self, agents_shared_outputs):
        """Verify lambda_layer_github_auth_arn output is available."""
        assert agents_shared_outputs.get("lambda_layer_github_auth_arn"), (
            "lambda_layer_github_auth_arn output not found in agents_shared. "
            "Run terraform apply in src/api/endpoints/agents/shared/"
        )


class TestECRRepositoryExistence:
    """Layer 3: Verify the ECR repository exists in AWS."""

    def test_01_ecr_repository_exists(self, ecr_client, agents_shared_outputs):
        """Verify the ECR repository exists in AWS."""
        repository_name = agents_shared_outputs.get("ecr_repository_name")
        if not repository_name:
            pytest.skip("ecr_repository_name output not available")
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[repository_name]
            )
            assert len(response["repositories"]) == 1, (
                f"Expected 1 repository named '{repository_name}', "
                f"got {len(response['repositories'])}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.fail(
                    f"ECR repository '{repository_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/agents/shared/"
                )
            raise


class TestECRRepositoryConfiguration:
    """Layer 4: Verify the ECR repository is configured correctly."""

    def test_01_ecr_repository_has_valid_uri(self, ecr_client, agents_shared_outputs):
        """Verify the ECR repository has a valid URI."""
        repository_name = agents_shared_outputs.get("ecr_repository_name")
        if not repository_name:
            pytest.skip("ecr_repository_name output not available")
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[repository_name]
            )
            repo = response["repositories"][0]
            assert "repositoryUri" in repo, (
                f"ECR repository '{repository_name}' missing repositoryUri"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("ECR repository does not exist")
            raise

    def test_02_ecr_repository_uri_matches_output(
        self, ecr_client, agents_shared_outputs
    ):
        """Verify the ECR repository URI matches the terraform output."""
        repository_name = agents_shared_outputs.get("ecr_repository_name")
        expected_url = agents_shared_outputs.get("ecr_repository_url")
        if not repository_name or not expected_url:
            pytest.skip("ECR outputs not available")
        try:
            response = ecr_client.describe_repositories(
                repositoryNames=[repository_name]
            )
            actual_uri = response["repositories"][0]["repositoryUri"]
            assert actual_uri == expected_url, (
                f"ECR repository URI mismatch. "
                f"Terraform output: {expected_url}, AWS: {actual_uri}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("ECR repository does not exist")
            raise


class TestECRRepositoryCapability:
    """Layer 5: Verify we can perform required ECR operations."""

    def test_01_can_list_images(self, ecr_client, agents_shared_outputs):
        """Verify we can list images in the ECR repository."""
        repository_name = agents_shared_outputs.get("ecr_repository_name")
        if not repository_name:
            pytest.skip("ecr_repository_name output not available")
        try:
            ecr_client.list_images(repositoryName=repository_name, maxResults=1)
        except ClientError as err:
            if err.response["Error"]["Code"] == "RepositoryNotFoundException":
                pytest.skip("ECR repository does not exist")
            if err.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail(
                    f"No permission to list images in ECR repository '{repository_name}'. "
                    "Check IAM permissions for ecr:ListImages."
                )
            raise


class TestLambdaLayerExistence:
    """Layer 3: Verify the Lambda layer exists in AWS."""

    def test_01_lambda_layer_exists(self, lambda_client, agents_shared_outputs):
        """Verify the Lambda layer exists in AWS."""
        layer_arn = agents_shared_outputs.get("lambda_layer_github_auth_arn")
        if not layer_arn:
            pytest.skip("lambda_layer_github_auth_arn output not available")
        try:
            # Use get_layer_version_by_arn to verify the exact layer version exists
            lambda_client.get_layer_version_by_arn(Arn=layer_arn)
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda layer '{layer_arn}' does not exist. "
                    "Run terraform apply in src/api/endpoints/agents/shared/"
                )
            raise


class TestLambdaLayerConfiguration:
    """Layer 4: Verify the Lambda layer is configured correctly."""

    def test_01_lambda_layer_compatible_with_python(
        self, lambda_client, agents_shared_outputs
    ):
        """Verify the Lambda layer is compatible with Python runtimes."""
        layer_arn = agents_shared_outputs.get("lambda_layer_github_auth_arn")
        if not layer_arn:
            pytest.skip("lambda_layer_github_auth_arn output not available")
        try:
            response = lambda_client.get_layer_version_by_arn(Arn=layer_arn)
            runtimes = response.get("CompatibleRuntimes", [])
            python_runtimes = [r for r in runtimes if r.startswith("python")]
            assert len(python_runtimes) > 0, (
                f"Lambda layer is not compatible with any Python runtime. "
                f"Compatible runtimes: {runtimes}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Lambda layer does not exist")
            raise

    def test_02_lambda_layer_has_description(
        self, lambda_client, agents_shared_outputs
    ):
        """Verify the Lambda layer has a description."""
        layer_arn = agents_shared_outputs.get("lambda_layer_github_auth_arn")
        if not layer_arn:
            pytest.skip("lambda_layer_github_auth_arn output not available")
        try:
            response = lambda_client.get_layer_version_by_arn(Arn=layer_arn)
            description = response.get("Description", "")
            assert description, (
                "Lambda layer has no description. "
                "Add a description for better maintainability."
            )
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Lambda layer does not exist")
            raise
