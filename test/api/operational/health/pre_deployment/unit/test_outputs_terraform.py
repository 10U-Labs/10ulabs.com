"""Unit tests for health endpoint outputs.tf configuration."""


def test_outputs_file_exists(health_src_dir):
    """Verify outputs.tf file exists."""
    assert (health_src_dir / "outputs.tf").exists()


def test_outputs_lambda_function_arn_defined(health_src_dir):
    """Verify lambda_function_arn output is defined."""
    content = (health_src_dir / "outputs.tf").read_text()
    assert 'output "lambda_function_arn"' in content


def test_outputs_lambda_function_arn_value(health_src_dir):
    """Verify lambda_function_arn references health_handler.arn."""
    content = (health_src_dir / "outputs.tf").read_text()
    assert "aws_lambda_function.health_handler.arn" in content


def test_outputs_lambda_function_name_defined(health_src_dir):
    """Verify lambda_function_name output is defined."""
    content = (health_src_dir / "outputs.tf").read_text()
    assert 'output "lambda_function_name"' in content


def test_outputs_lambda_function_name_value(health_src_dir):
    """Verify lambda_function_name references health_handler.function_name."""
    content = (health_src_dir / "outputs.tf").read_text()
    assert "aws_lambda_function.health_handler.function_name" in content


def test_outputs_log_group_name_defined(health_src_dir):
    """Verify log_group_name output is defined."""
    content = (health_src_dir / "outputs.tf").read_text()
    assert 'output "log_group_name"' in content


def test_outputs_log_group_name_value(health_src_dir):
    """Verify log_group_name references health_handler log group."""
    content = (health_src_dir / "outputs.tf").read_text()
    assert "aws_cloudwatch_log_group.health_handler.name" in content


def test_outputs_has_three_outputs(health_src_dir):
    """Verify outputs.tf contains exactly three outputs."""
    content = (health_src_dir / "outputs.tf").read_text()
    output_count = content.count('output "')
    assert output_count == 3, f"Expected 3 outputs, found {output_count}"
