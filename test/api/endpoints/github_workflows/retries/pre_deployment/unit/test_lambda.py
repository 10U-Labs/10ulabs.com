"""Unit tests for lambda.tf configuration."""


class TestLambdaConfiguration:
    """Tests for lambda.tf Terraform configuration."""

    def test_lambda_file_exists(self, retries_src_path):
        """Lambda.tf file exists."""
        assert (retries_src_path / "lambda.tf").exists()

    def test_lambda_function_resource_exists(self, retries_src_path):
        """Lambda function resource is defined."""
        with open(retries_src_path / "lambda.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'resource "aws_lambda_function"' in content

    def test_lambda_uses_python_runtime(self, retries_src_path):
        """Lambda uses Python runtime."""
        with open(retries_src_path / "lambda.tf", encoding="utf-8") as f:
            content = f.read()
        assert "python3" in content

    def test_lambda_has_handler(self, retries_src_path):
        """Lambda specifies handler."""
        with open(retries_src_path / "lambda.tf", encoding="utf-8") as f:
            content = f.read()
        assert "handler" in content

    def test_lambda_has_timeout(self, retries_src_path):
        """Lambda specifies timeout."""
        with open(retries_src_path / "lambda.tf", encoding="utf-8") as f:
            content = f.read()
        assert "timeout" in content

    def test_lambda_has_memory_size(self, retries_src_path):
        """Lambda specifies memory_size."""
        with open(retries_src_path / "lambda.tf", encoding="utf-8") as f:
            content = f.read()
        assert "memory_size" in content

    def test_lambda_has_environment_variables(self, retries_src_path):
        """Lambda has environment variables block."""
        with open(retries_src_path / "lambda.tf", encoding="utf-8") as f:
            content = f.read()
        assert "environment" in content

    def test_lambda_has_github_token_env_var(self, retries_src_path):
        """Lambda has GITHUB_TOKEN_SECRET_NAME environment variable."""
        with open(retries_src_path / "lambda.tf", encoding="utf-8") as f:
            content = f.read()
        assert "GITHUB_TOKEN_SECRET_NAME" in content

    def test_lambda_has_logging_config(self, retries_src_path):
        """Lambda has logging_config block."""
        with open(retries_src_path / "lambda.tf", encoding="utf-8") as f:
            content = f.read()
        assert "logging_config" in content

    def test_cloudwatch_log_group_exists(self, retries_src_path):
        """CloudWatch log group resource is defined."""
        with open(retries_src_path / "lambda.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'resource "aws_cloudwatch_log_group"' in content

    def test_archive_file_data_source_exists(self, retries_src_path):
        """Archive file data source is defined."""
        with open(retries_src_path / "lambda.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'data "archive_file"' in content
