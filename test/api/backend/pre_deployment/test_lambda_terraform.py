from pathlib import Path


def test_lambda_terraform_file_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "lambda.tf"
    file_exists = lambda_file.exists()
    assert file_exists


def test_catchall_handler_archive_file_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    contains_archive_file = 'data "archive_file" "catchall_handler"' in content
    assert contains_archive_file


def test_catchall_handler_lambda_function_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    contains_lambda_function = 'resource "aws_lambda_function" "catchall_handler"' in content
    assert contains_lambda_function


def test_catchall_handler_cloudwatch_log_group_exists():
    lambda_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "lambda.tf"
    with open(lambda_file, encoding="utf-8") as f:
        content = f.read()
    contains_log_group = 'resource "aws_cloudwatch_log_group" "catchall_handler"' in content
    assert contains_log_group
