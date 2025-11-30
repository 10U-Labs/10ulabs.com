from pathlib import Path


def test_lambda_terraform_file_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    assert lambda_file.exists()


def test_catchall_handler_archive_file_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "catchall_handler"' in content


def test_catchall_handler_lambda_function_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "catchall_handler"' in content


def test_catchall_handler_cloudwatch_log_group_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "catchall_handler"' in content


def test_runners_handler_archive_file_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "runners_handler"' in content


def test_runners_handler_lambda_function_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "runners_handler"' in content


def test_runners_handler_has_sqs_event_source():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_event_source_mapping" "runners_handler_sqs"' in content


def test_runners_handler_cloudwatch_log_group_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "runners_handler"' in content


def test_v1_handler_archive_file_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "v1_handler"' in content


def test_v1_handler_lambda_function_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "v1_handler"' in content


def test_v1_handler_cloudwatch_log_group_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "v1_handler"' in content


def test_circuit_breaker_remediation_archive_file_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "circuit_breaker_remediation"' in content


def test_circuit_breaker_remediation_lambda_function_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "circuit_breaker_remediation"' in content


def test_circuit_breaker_remediation_cloudwatch_log_group_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "circuit_breaker_remediation"' in content


def test_dlq_reprocessor_archive_file_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "dlq_reprocessor"' in content


def test_dlq_reprocessor_lambda_function_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "dlq_reprocessor"' in content


def test_dlq_reprocessor_cloudwatch_log_group_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "dlq_reprocessor"' in content


def test_circuit_breaker_recovery_archive_file_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "archive_file" "circuit_breaker_recovery"' in content


def test_circuit_breaker_recovery_lambda_function_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_lambda_function" "circuit_breaker_recovery"' in content


def test_circuit_breaker_recovery_cloudwatch_log_group_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_cloudwatch_log_group" "circuit_breaker_recovery"' in content


def test_lambda_functions_use_memory_variable():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'var.lambda_memory_mb' in content


def test_lambda_functions_use_timeout_variable():
    lambda_file = Path(__file__).parent.parent.parent.parent / "src" / "api" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    assert 'var.lambda_timeout_seconds' in content
