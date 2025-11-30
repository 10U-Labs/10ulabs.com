from pathlib import Path


def test_iam_terraform_file_exists():
    iam_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "iam.tf"
    assert iam_file.exists()


def test_health_handler_iam_role_exists():
    iam_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "lambda_health_handler"' in content


def test_health_handler_iam_role_has_lambda_assume_role():
    iam_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'lambda.amazonaws.com' in content


def test_health_handler_has_basic_execution_role_attachment():
    iam_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy_attachment" "lambda_health_handler_basic"' in content


def test_health_handler_uses_basic_execution_policy():
    iam_file = Path(__file__).parent.parent.parent.parent / "src" / "health" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    assert 'AWSLambdaBasicExecutionRole' in content
