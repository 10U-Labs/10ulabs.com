def test_lambda_edge_file_exists(src_dir):
    assert (src_dir / "lambda_edge.tf").exists()


def test_archive_file_data_source_defined(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert 'data "archive_file" "spa_routing"' in content


def test_archive_file_type_zip(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert 'type        = "zip"' in content


def test_archive_source_file_spa_routing(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert "lambda/handler.py" in content


def test_iam_role_defined(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert 'resource "aws_iam_role" "spa_routing"' in content


def test_iam_role_uses_us_east_1_provider(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert "provider = aws.us-east-1" in content


def test_iam_role_trust_lambda_service(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert '"lambda.amazonaws.com"' in content


def test_iam_role_trust_edge_lambda_service(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert '"edgelambda.amazonaws.com"' in content


def test_iam_role_policy_attachment_defined(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert 'resource "aws_iam_role_policy_attachment" "spa_routing_basic"' in content


def test_iam_role_policy_attachment_uses_us_east_1_provider(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    attachment_section = content.split('resource "aws_iam_role_policy_attachment"')[1]
    assert "provider   = aws.us-east-1" in attachment_section


def test_iam_role_policy_basic_execution(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert "AWSLambdaBasicExecutionRole" in content


def test_cloudwatch_log_group_defined(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert 'resource "aws_cloudwatch_log_group" "spa_routing"' in content


def test_cloudwatch_log_group_us_east_1_provider(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    log_group_section = content.split('resource "aws_cloudwatch_log_group"')[1]
    assert "provider          = aws.us-east-1" in log_group_section


def test_cloudwatch_log_group_retention_7_days(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert "retention_in_days = 7" in content


def test_lambda_function_defined(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert 'resource "aws_lambda_function" "spa_routing"' in content


def test_lambda_function_us_east_1_provider(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    lambda_section = content.split('resource "aws_lambda_function"')[1]
    assert "provider         = aws.us-east-1" in lambda_section


def test_lambda_function_handler_config(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert 'handler          = "handler.lambda_handler"' in content


def test_lambda_function_runtime_python312(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert 'runtime          = "python3.12"' in content


def test_lambda_function_timeout(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert "timeout          = 5" in content


def test_lambda_function_memory_128(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert "memory_size      = 128" in content


def test_lambda_function_publish_true(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert "publish          = true" in content


def test_lambda_function_description(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert "Lambda@Edge handler for SPA routing" in content


def test_lambda_function_logging_config(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert "logging_config {" in content


def test_lambda_function_log_format_text(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert 'log_format = "Text"' in content


def test_lambda_function_uses_source_code_hash(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert "source_code_hash = data.archive_file.spa_routing.output_base64sha256" in content


def test_lambda_function_lifecycle_replace_triggered(src_dir):
    content = (src_dir / "lambda_edge.tf").read_text()
    assert "replace_triggered_by = [aws_iam_role.spa_routing.id]" in content
