from pathlib import Path


def test_iam_terraform_file_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    file_exists = iam_file.exists()
    assert file_exists


def test_lambda_catchall_handler_role_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    role_exists = 'resource "aws_iam_role" "lambda_catchall_handler"' in content
    assert role_exists
