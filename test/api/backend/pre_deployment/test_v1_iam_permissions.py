import re
from pathlib import Path


def get_lambda_source():
    lambda_path = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "lambdas" / "v1.py"
    with open(lambda_path, 'r', encoding='utf-8') as f:
        return f.read()


def get_iam_terraform():
    iam_path = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "iam.tf"
    with open(iam_path, 'r', encoding='utf-8') as f:
        return f.read()


def extract_ec2_api_calls(source_code):
    ec2_client_pattern = r'get_ec2_client\(\)\.([\w_]+)\s*\('
    matches = re.findall(ec2_client_pattern, source_code)
    return set(matches)


def convert_boto3_to_iam_action(boto3_method):
    words = boto3_method.split('_')
    pascal_case = ''.join(word.capitalize() for word in words)
    return f"ec2:{pascal_case}"


def extract_ec2_iam_permissions(terraform_content):
    v1_handler_section = re.search(
        r'resource\s+"aws_iam_role_policy"\s+"lambda_v1_handler_ec2".*?policy\s*=\s*jsonencode\(\{.*?Action\s*=\s*\[(.*?)\]',
        terraform_content,
        re.DOTALL
    )
    permissions = set()
    if v1_handler_section:
        actions_block = v1_handler_section.group(1)
        action_pattern = r'"(ec2:\w+)"'
        permissions = set(re.findall(action_pattern, actions_block))
    return permissions


class TestV1LambdaEc2IamPermissions:

    def test_describe_vpcs_permission_exists(self):
        iam_content = get_iam_terraform()
        permissions = extract_ec2_iam_permissions(iam_content)

        assert "ec2:DescribeVpcs" in permissions

    def test_describe_subnets_permission_exists(self):
        iam_content = get_iam_terraform()
        permissions = extract_ec2_iam_permissions(iam_content)

        assert "ec2:DescribeSubnets" in permissions

    def test_describe_security_groups_permission_exists(self):
        iam_content = get_iam_terraform()
        permissions = extract_ec2_iam_permissions(iam_content)

        assert "ec2:DescribeSecurityGroups" in permissions

    def test_describe_instances_permission_exists(self):
        iam_content = get_iam_terraform()
        permissions = extract_ec2_iam_permissions(iam_content)

        assert "ec2:DescribeInstances" in permissions

    def test_describe_images_permission_exists(self):
        iam_content = get_iam_terraform()
        permissions = extract_ec2_iam_permissions(iam_content)

        assert "ec2:DescribeImages" in permissions

    def test_run_instances_permission_exists(self):
        iam_content = get_iam_terraform()
        permissions = extract_ec2_iam_permissions(iam_content)

        assert "ec2:RunInstances" in permissions

    def test_terminate_instances_permission_exists(self):
        iam_content = get_iam_terraform()
        permissions = extract_ec2_iam_permissions(iam_content)

        assert "ec2:TerminateInstances" in permissions

    def test_all_ec2_api_calls_have_iam_permissions(self):
        source_code = get_lambda_source()
        iam_content = get_iam_terraform()
        ec2_calls = extract_ec2_api_calls(source_code)
        iam_permissions = extract_ec2_iam_permissions(iam_content)
        required_permissions = {convert_boto3_to_iam_action(call) for call in ec2_calls}
        missing = required_permissions - iam_permissions

        assert missing == set()
