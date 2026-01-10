"""Pre-deployment integration tests for retries Terraform configuration."""
from pathlib import Path

import pytest


class TestTerraformFilesExist:
    """Tests that required Terraform files exist."""

    def test_backend_tf_exists(self, terraform_dir: Path):
        """Backend configuration file exists."""
        assert (terraform_dir / "backend.tf").exists()

    def test_providers_tf_exists(self, terraform_dir: Path):
        """Providers configuration file exists."""
        assert (terraform_dir / "providers.tf").exists()

    def test_shared_tf_exists(self, terraform_dir: Path):
        """Shared module configuration file exists."""
        assert (terraform_dir / "shared.tf").exists()

    def test_locals_tf_exists(self, terraform_dir: Path):
        """Locals configuration file exists."""
        assert (terraform_dir / "locals.tf").exists()

    def test_lambda_tf_exists(self, terraform_dir: Path):
        """Lambda configuration file exists."""
        assert (terraform_dir / "lambda.tf").exists()

    def test_iam_tf_exists(self, terraform_dir: Path):
        """IAM configuration file exists."""
        assert (terraform_dir / "iam.tf").exists()

    def test_sqs_tf_exists(self, terraform_dir: Path):
        """SQS configuration file exists."""
        assert (terraform_dir / "sqs.tf").exists()

    def test_outputs_tf_exists(self, terraform_dir: Path):
        """Outputs configuration file exists."""
        assert (terraform_dir / "outputs.tf").exists()

    def test_lambda_handler_exists(self, terraform_dir: Path):
        """Lambda handler Python file exists."""
        assert (terraform_dir / "lambda" / "handler.py").exists()
