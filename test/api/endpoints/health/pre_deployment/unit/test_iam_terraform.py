"""Unit tests for health endpoint IAM Terraform configuration."""
from test.api.endpoints.health.conftest import HEALTH_SRC

IAM_FILE = HEALTH_SRC / "iam.tf"


def test_iam_terraform_file_exists():
    """Verify iam.tf file exists."""
    assert IAM_FILE.exists()


def test_health_handler_iam_role_exists():
    """Verify IAM role resource is defined."""
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "lambda_health_handler"' in content


def test_health_handler_iam_role_has_lambda_assume_role():
    """Verify IAM role allows Lambda assume role."""
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'lambda.amazonaws.com' in content


def test_health_handler_has_basic_execution_role_attachment():
    """Verify basic execution role attachment exists."""
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy_attachment" "lambda_health_handler_basic"' in content


def test_health_handler_uses_basic_execution_policy():
    """Verify basic execution policy is used."""
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'AWSLambdaBasicExecutionRole' in content


def test_health_handler_has_ec2_describe_permissions():
    """Verify EC2 describe permissions policy exists."""
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "lambda_health_handler_ec2_describe"' in content


def test_health_handler_can_describe_security_groups():
    """Verify ec2:DescribeSecurityGroups permission."""
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'ec2:DescribeSecurityGroups' in content


def test_health_handler_can_describe_subnets():
    """Verify ec2:DescribeSubnets permission."""
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'ec2:DescribeSubnets' in content


def test_health_handler_can_describe_vpcs():
    """Verify ec2:DescribeVpcs permission."""
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'ec2:DescribeVpcs' in content
