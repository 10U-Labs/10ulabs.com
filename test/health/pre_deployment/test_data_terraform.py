from pathlib import Path


def test_data_terraform_file_exists():
    data_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "data.tf"
    assert data_file.exists()


def test_import_block_for_iam_role_exists():
    data_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "data.tf"
    with open(data_file, encoding="utf-8") as f:
        content = f.read()
    assert 'to = aws_iam_role.lambda_health_handler' in content


def test_import_block_for_cloudwatch_log_group_exists():
    data_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "data.tf"
    with open(data_file, encoding="utf-8") as f:
        content = f.read()
    assert 'to = aws_cloudwatch_log_group.health_handler' in content


def test_import_block_for_lambda_function_exists():
    data_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "data.tf"
    with open(data_file, encoding="utf-8") as f:
        content = f.read()
    assert 'to = aws_lambda_function.health_handler' in content
