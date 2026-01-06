"""Unit tests for health endpoint lambda.tf configuration."""


def test_lambda_file_exists(health_src_dir):
    """Verify lambda.tf file exists."""
    assert (health_src_dir / "lambda.tf").exists()


def test_lambda_archive_file_data_source(health_src_dir):
    """Verify archive_file data source for Lambda packaging."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert 'data "archive_file" "health_handler"' in content


def test_lambda_archive_type_is_zip(health_src_dir):
    """Verify archive type is zip."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert 'type        = "zip"' in content


def test_lambda_function_resource_exists(health_src_dir):
    """Verify Lambda function resource is defined."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert 'resource "aws_lambda_function" "health_handler"' in content


def test_lambda_function_uses_variable_name(health_src_dir):
    """Verify Lambda function name uses variable."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert "function_name    = var.health_handler_function_name" in content


def test_lambda_function_uses_iam_role(health_src_dir):
    """Verify Lambda function references IAM role."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert "role             = aws_iam_role.lambda_health_handler.arn" in content


def test_lambda_function_handler_is_handler_handler(health_src_dir):
    """Verify Lambda function handler is set correctly."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert 'handler          = "handler.handler"' in content


def test_lambda_function_runtime_is_python313(health_src_dir):
    """Verify Lambda function uses Python 3.13 runtime."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert 'runtime          = "python3.13"' in content


def test_lambda_function_architecture_is_arm64(health_src_dir):
    """Verify Lambda function uses ARM64 architecture."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert 'architectures    = ["arm64"]' in content


def test_lambda_function_timeout_is_10(health_src_dir):
    """Verify Lambda function has 10 second timeout."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert "timeout          = 10" in content


def test_lambda_function_has_description(health_src_dir):
    """Verify Lambda function has a description."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert 'description      = "Health check endpoint for API"' in content


def test_lambda_function_has_logging_config_block(health_src_dir):
    """Verify Lambda function has logging_config block."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert "logging_config {" in content


def test_lambda_function_log_format_is_text(health_src_dir):
    """Verify Lambda function log format is Text."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert 'log_format = "Text"' in content


def test_lambda_function_has_tags(health_src_dir):
    """Verify Lambda function has tags configured."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert "tags = merge(local.common_tags" in content


def test_lambda_cloudwatch_log_group_exists(health_src_dir):
    """Verify CloudWatch log group resource is defined."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert 'resource "aws_cloudwatch_log_group" "health_handler"' in content


def test_lambda_cloudwatch_log_group_uses_variable(health_src_dir):
    """Verify CloudWatch log group uses variable for name."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert "name              = var.health_handler_log_group_name" in content


def test_lambda_cloudwatch_log_group_retention_7_days(health_src_dir):
    """Verify CloudWatch log group has 7 day retention."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert "retention_in_days = 7" in content


def test_lambda_permission_resource_exists(health_src_dir):
    """Verify Lambda permission resource is defined."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert 'resource "aws_lambda_permission" "api_gateway"' in content


def test_lambda_permission_principal_is_api_gateway(health_src_dir):
    """Verify Lambda permission principal is API Gateway."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert 'principal     = "apigateway.amazonaws.com"' in content


def test_lambda_permission_statement_id(health_src_dir):
    """Verify Lambda permission has correct statement ID."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert 'statement_id  = "AllowAPIGatewayInvoke"' in content


def test_lambda_permission_action(health_src_dir):
    """Verify Lambda permission uses correct action."""
    content = (health_src_dir / "lambda.tf").read_text()
    assert 'action        = "lambda:InvokeFunction"' in content
