from pathlib import Path


def test_iam_terraform_file_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api" / "endpoints" / "ec2_runner" / "iam.tf"
    file_exists = iam_file.exists()
    assert file_exists


def test_ec2_runner_role_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api" / "endpoints" / "ec2_runner" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    role_exists = 'resource "aws_iam_role" "ec2_runner"' in content
    assert role_exists


def test_ec2_runner_ssm_policy_attachment_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api" / "endpoints" / "ec2_runner" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    policy_exists = 'resource "aws_iam_role_policy_attachment" "ec2_runner_ssm_policy"' in content
    assert policy_exists


def test_ec2_runner_ecr_access_policy_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api" / "endpoints" / "ec2_runner" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    policy_exists = 'resource "aws_iam_role_policy" "ec2_runner_ecr_access"' in content
    assert policy_exists


def test_ec2_runner_self_terminate_policy_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api" / "endpoints" / "ec2_runner" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    policy_exists = 'resource "aws_iam_role_policy" "ec2_runner_self_terminate"' in content
    assert policy_exists


def test_ec2_instance_profile_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api" / "endpoints" / "ec2_runner" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    profile_exists = 'resource "aws_iam_instance_profile" "ec2_runner"' in content
    assert profile_exists


def test_lambda_role_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api" / "endpoints" / "ec2_runner" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    role_exists = 'resource "aws_iam_role" "lambda"' in content
    assert role_exists


def test_lambda_basic_policy_attachment_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api" / "endpoints" / "ec2_runner" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    policy_exists = 'resource "aws_iam_role_policy_attachment" "lambda_basic"' in content
    assert policy_exists


def test_ec2_access_policy_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api" / "endpoints" / "ec2_runner" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    policy_exists = 'resource "aws_iam_role_policy" "ec2_access"' in content
    assert policy_exists


def test_iam_pass_role_policy_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api" / "endpoints" / "ec2_runner" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    policy_exists = 'resource "aws_iam_role_policy" "iam_pass_role"' in content
    assert policy_exists


def test_ssm_access_policy_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api" / "endpoints" / "ec2_runner" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    policy_exists = 'resource "aws_iam_role_policy" "ssm_access"' in content
    assert policy_exists


def test_kms_access_policy_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api" / "endpoints" / "ec2_runner" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    policy_exists = 'resource "aws_iam_role_policy" "kms_access"' in content
    assert policy_exists


def test_dynamodb_access_policy_exists():
    iam_file = Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "api" / "endpoints" / "ec2_runner" / "iam.tf"
    with open(iam_file, encoding="utf-8") as f:
        content = f.read()
    policy_exists = 'resource "aws_iam_role_policy" "dynamodb_access"' in content
    assert policy_exists
