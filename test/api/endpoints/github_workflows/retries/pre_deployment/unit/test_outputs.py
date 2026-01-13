"""Unit tests for outputs.tf configuration."""


class TestOutputsConfiguration:
    """Tests for outputs.tf Terraform configuration."""

    def test_outputs_file_exists(self, retries_src_path):
        """Outputs.tf file exists."""
        assert (retries_src_path / "outputs.tf").exists()

    def test_lambda_function_arn_output_exists(self, retries_src_path):
        """Lambda function ARN output is defined."""
        with open(retries_src_path / "outputs.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'output "lambda_function_arn"' in content

    def test_lambda_function_arn_has_description(self, retries_src_path):
        """Lambda function ARN output has description."""
        with open(retries_src_path / "outputs.tf", encoding="utf-8") as f:
            content = f.read()
        assert "description" in content

    def test_lambda_function_arn_references_handler(self, retries_src_path):
        """Lambda function ARN output references handler resource."""
        with open(retries_src_path / "outputs.tf", encoding="utf-8") as f:
            content = f.read()
        assert "aws_lambda_function.handler.arn" in content

    def test_lambda_function_name_output_exists(self, retries_src_path):
        """Lambda function name output is defined."""
        with open(retries_src_path / "outputs.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'output "lambda_function_name"' in content

    def test_lambda_function_name_references_handler(self, retries_src_path):
        """Lambda function name output references handler resource."""
        with open(retries_src_path / "outputs.tf", encoding="utf-8") as f:
            content = f.read()
        assert "aws_lambda_function.handler.function_name" in content

    def test_sqs_queue_url_output_exists(self, retries_src_path):
        """SQS queue URL output is defined."""
        with open(retries_src_path / "outputs.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'output "sqs_queue_url"' in content

    def test_sqs_queue_url_references_main_queue(self, retries_src_path):
        """SQS queue URL output references main queue."""
        with open(retries_src_path / "outputs.tf", encoding="utf-8") as f:
            content = f.read()
        assert "aws_sqs_queue.main.url" in content

    def test_sqs_queue_arn_output_exists(self, retries_src_path):
        """SQS queue ARN output is defined."""
        with open(retries_src_path / "outputs.tf", encoding="utf-8") as f:
            content = f.read()
        assert 'output "sqs_queue_arn"' in content

    def test_sqs_queue_arn_references_main_queue(self, retries_src_path):
        """SQS queue ARN output references main queue."""
        with open(retries_src_path / "outputs.tf", encoding="utf-8") as f:
            content = f.read()
        assert "aws_sqs_queue.main.arn" in content
