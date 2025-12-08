"""Unit tests for EC2 runner IAM Terraform configuration."""
from ...conftest import EC2_RUNNER_SRC

IAM_FILE = EC2_RUNNER_SRC / "iam.tf"


def test_iam_terraform_file_exists():
    """Test that iam.tf file exists."""
    assert IAM_FILE.exists()


def test_ec2_runner_role_exists():
    """Test that EC2 runner IAM role is defined."""
    content = IAM_FILE.read_text(encoding="utf-8")
    assert 'resource "aws_iam_role" "ec2_runner"' in content


def test_ec2_runner_ssm_policy_attachment_exists():
    """Test that EC2 runner SSM policy attachment is defined."""
    content = IAM_FILE.read_text(encoding="utf-8")
    assert 'resource "aws_iam_role_policy_attachment" "ec2_runner_ssm_policy"' in content


def test_ec2_runner_ecr_access_policy_exists():
    """Test that EC2 runner ECR access policy is defined."""
    content = IAM_FILE.read_text(encoding="utf-8")
    assert 'resource "aws_iam_role_policy" "ec2_runner_ecr_access"' in content


def test_ec2_runner_self_terminate_policy_exists():
    """Test that EC2 runner self-terminate policy is defined."""
    content = IAM_FILE.read_text(encoding="utf-8")
    assert 'resource "aws_iam_role_policy" "ec2_runner_self_terminate"' in content


def test_ec2_instance_profile_exists():
    """Test that EC2 instance profile is defined."""
    content = IAM_FILE.read_text(encoding="utf-8")
    assert 'resource "aws_iam_instance_profile" "ec2_runner"' in content


def test_lambda_role_exists():
    """Test that Lambda IAM role is defined."""
    content = IAM_FILE.read_text(encoding="utf-8")
    assert 'resource "aws_iam_role" "lambda"' in content


def test_lambda_basic_policy_attachment_exists():
    """Test that Lambda basic policy attachment is defined."""
    content = IAM_FILE.read_text(encoding="utf-8")
    assert 'resource "aws_iam_role_policy_attachment" "lambda_basic"' in content


def test_ec2_access_policy_exists():
    """Test that EC2 access policy is defined."""
    content = IAM_FILE.read_text(encoding="utf-8")
    assert 'resource "aws_iam_role_policy" "ec2_access"' in content


def test_iam_pass_role_policy_exists():
    """Test that IAM pass role policy is defined."""
    content = IAM_FILE.read_text(encoding="utf-8")
    assert 'resource "aws_iam_role_policy" "iam_pass_role"' in content


def test_ssm_access_policy_exists():
    """Test that SSM access policy is defined."""
    content = IAM_FILE.read_text(encoding="utf-8")
    assert 'resource "aws_iam_role_policy" "ssm_access"' in content


def test_kms_access_policy_exists():
    """Test that KMS access policy is defined."""
    content = IAM_FILE.read_text(encoding="utf-8")
    assert 'resource "aws_iam_role_policy" "kms_access"' in content


def test_dynamodb_access_policy_exists():
    """Test that DynamoDB access policy is defined."""
    content = IAM_FILE.read_text(encoding="utf-8")
    assert 'resource "aws_iam_role_policy" "dynamodb_access"' in content
