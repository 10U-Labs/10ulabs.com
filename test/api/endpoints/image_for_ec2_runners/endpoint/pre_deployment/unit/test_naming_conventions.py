"""Unit tests to verify IAM role and Lambda function names use PascalCase.

These tests parse Terraform files to validate naming conventions before deployment.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
from repo_utils import REPO_ROOT
from test_fixtures.terraform_tests import create_naming_conventions_tests

IMAGE_EC2_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ec2_runners"

TestIAMRoleNamingConventions, TestLambdaFunctionNamingConventions = (
    create_naming_conventions_tests(endpoint_src=IMAGE_EC2_SRC, use_handler_names=True)
)
