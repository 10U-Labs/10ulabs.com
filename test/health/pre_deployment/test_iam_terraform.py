from test.health.conftest import HEALTH_SRC

IAM_FILE = HEALTH_SRC / "iam.tf"


def test_iam_terraform_file_exists():
    assert IAM_FILE.exists()


def test_health_handler_iam_role_exists():
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role" "lambda_health_handler"' in content


def test_health_handler_iam_role_has_lambda_assume_role():
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'lambda.amazonaws.com' in content


def test_health_handler_has_basic_execution_role_attachment():
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy_attachment" "lambda_health_handler_basic"' in content


def test_health_handler_uses_basic_execution_policy():
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'AWSLambdaBasicExecutionRole' in content


def test_health_handler_has_ec2_describe_permissions():
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_iam_role_policy" "lambda_health_handler_ec2_describe"' in content


def test_health_handler_can_describe_security_groups():
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'ec2:DescribeSecurityGroups' in content


def test_health_handler_can_describe_subnets():
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'ec2:DescribeSubnets' in content


def test_health_handler_can_describe_vpcs():
    with open(IAM_FILE, encoding="utf-8") as f:
        content = f.read()
    assert 'ec2:DescribeVpcs' in content
