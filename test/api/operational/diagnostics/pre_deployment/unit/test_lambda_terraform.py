"""Unit tests for diagnostics endpoint lambda.tf configuration."""


def test_lambda_file_exists(diagnostics_src_dir):
    """Verify lambda.tf file exists."""
    assert (diagnostics_src_dir / "lambda.tf").exists()


def test_lambda_archive_file_data_source(diagnostics_src_dir):
    """Verify archive_file data source for Lambda packaging."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'data "archive_file" "diagnostics_handler"' in content


def test_lambda_archive_type_is_zip(diagnostics_src_dir):
    """Verify archive type is zip."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'type = "zip"' in content


def test_lambda_archive_includes_handler(diagnostics_src_dir):
    """Verify archive includes handler.py."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'filename = "handler.py"' in content


def test_lambda_archive_includes_lambda_http(diagnostics_src_dir):
    """Verify archive includes lambda_http module."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'filename = "lambda_http.py"' in content


def test_lambda_function_resource_exists(diagnostics_src_dir):
    """Verify Lambda function resource is defined."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'resource "aws_lambda_function" "diagnostics_handler"' in content


def test_lambda_function_uses_variable_name(diagnostics_src_dir):
    """Verify Lambda function name uses variable."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert "function_name    = var.diagnostics_handler_function_name" in content


def test_lambda_function_uses_iam_role(diagnostics_src_dir):
    """Verify Lambda function references IAM role."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert "role             = aws_iam_role.lambda_diagnostics_handler.arn" in content


def test_lambda_function_handler_is_handler_handler(diagnostics_src_dir):
    """Verify Lambda function handler is set correctly."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'handler          = "handler.handler"' in content


def test_lambda_function_runtime_is_python313(diagnostics_src_dir):
    """Verify Lambda function uses Python 3.13 runtime."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'runtime          = "python3.13"' in content


def test_lambda_function_architecture_is_arm64(diagnostics_src_dir):
    """Verify Lambda function uses ARM64 architecture."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'architectures    = ["arm64"]' in content


def test_lambda_function_timeout_is_10(diagnostics_src_dir):
    """Verify Lambda function has 10 second timeout."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert "timeout          = 10" in content


def test_lambda_function_has_description(diagnostics_src_dir):
    """Verify Lambda function has a description."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'description      = "Diagnostics endpoint for API"' in content


def test_lambda_function_has_logging_config_block(diagnostics_src_dir):
    """Verify Lambda function has logging_config block."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert "logging_config {" in content


def test_lambda_function_log_format_is_text(diagnostics_src_dir):
    """Verify Lambda function log format is Text."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'log_format = "Text"' in content


def test_lambda_function_has_tags(diagnostics_src_dir):
    """Verify Lambda function has tags configured."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert "tags = merge(local.common_tags" in content


def test_lambda_cloudwatch_log_group_exists(diagnostics_src_dir):
    """Verify CloudWatch log group resource is defined."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'resource "aws_cloudwatch_log_group" "diagnostics_handler"' in content


def test_lambda_cloudwatch_log_group_uses_variable(diagnostics_src_dir):
    """Verify CloudWatch log group uses variable for name."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert "name              = var.diagnostics_handler_log_group_name" in content


def test_lambda_cloudwatch_log_group_retention_7_days(diagnostics_src_dir):
    """Verify CloudWatch log group has 7 day retention."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert "retention_in_days = 7" in content


def test_lambda_permission_resource_exists(diagnostics_src_dir):
    """Verify Lambda permission resource is defined."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'resource "aws_lambda_permission" "api_gateway"' in content


def test_lambda_permission_principal_is_api_gateway(diagnostics_src_dir):
    """Verify Lambda permission principal is API Gateway."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'principal     = "apigateway.amazonaws.com"' in content


def test_lambda_permission_statement_id(diagnostics_src_dir):
    """Verify Lambda permission has correct statement ID."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'statement_id  = "AllowAPIGatewayInvoke"' in content


def test_lambda_permission_action(diagnostics_src_dir):
    """Verify Lambda permission uses correct action."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert 'action        = "lambda:InvokeFunction"' in content


def test_lambda_permission_source_arn_uses_locals(diagnostics_src_dir):
    """Verify Lambda permission source ARN uses local values."""
    content = (diagnostics_src_dir / "lambda.tf").read_text()
    assert "local.aws_region" in content
    assert "local.aws_account_id" in content
