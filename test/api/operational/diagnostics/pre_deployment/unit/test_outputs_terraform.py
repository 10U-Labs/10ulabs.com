def test_outputs_file_exists(diagnostics_src_dir):
    assert (diagnostics_src_dir / "outputs.tf").exists()


def test_outputs_lambda_function_arn_defined(diagnostics_src_dir):
    content = (diagnostics_src_dir / "outputs.tf").read_text()
    assert 'output "lambda_function_arn"' in content


def test_outputs_lambda_function_arn_value(diagnostics_src_dir):
    content = (diagnostics_src_dir / "outputs.tf").read_text()
    assert "aws_lambda_function.diagnostics_handler.arn" in content


def test_outputs_lambda_function_name_defined(diagnostics_src_dir):
    content = (diagnostics_src_dir / "outputs.tf").read_text()
    assert 'output "lambda_function_name"' in content


def test_outputs_lambda_function_name_value(diagnostics_src_dir):
    content = (diagnostics_src_dir / "outputs.tf").read_text()
    assert "aws_lambda_function.diagnostics_handler.function_name" in content


def test_outputs_log_group_name_defined(diagnostics_src_dir):
    content = (diagnostics_src_dir / "outputs.tf").read_text()
    assert 'output "log_group_name"' in content


def test_outputs_log_group_name_value(diagnostics_src_dir):
    content = (diagnostics_src_dir / "outputs.tf").read_text()
    assert "aws_cloudwatch_log_group.diagnostics_handler.name" in content


def test_outputs_has_three_outputs(diagnostics_src_dir):
    content = (diagnostics_src_dir / "outputs.tf").read_text()
    output_count = content.count('output "')
    assert output_count == 3, f"Expected 3 outputs, found {output_count}"
