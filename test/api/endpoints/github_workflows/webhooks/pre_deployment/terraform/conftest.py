"""Pytest fixtures for github_workflows/webhooks Terraform unit tests."""

import pytest

from repo_utils import REPO_ROOT

TERRAFORM_DIR = (
    REPO_ROOT / "src" / "api" / "endpoints" / "github_workflows" / "webhooks"
)


@pytest.fixture(name="terraform_dir")
def fixture_terraform_dir():
    """Provide path to github_workflows/webhooks Terraform directory."""
    return TERRAFORM_DIR


@pytest.fixture(name="lambda_tf_content")
def fixture_lambda_tf_content(terraform_dir):
    """Provide lambda.tf file content."""
    return (terraform_dir / "lambda.tf").read_text()


@pytest.fixture(name="iam_tf_content")
def fixture_iam_tf_content(terraform_dir):
    """Provide iam.tf file content."""
    return (terraform_dir / "iam.tf").read_text()


@pytest.fixture(name="sqs_tf_content")
def fixture_sqs_tf_content(terraform_dir):
    """Provide sqs.tf file content."""
    return (terraform_dir / "sqs.tf").read_text()


@pytest.fixture(name="dynamodb_tf_content")
def fixture_dynamodb_tf_content(terraform_dir):
    """Provide dynamodb.tf file content."""
    return (terraform_dir / "dynamodb.tf").read_text()


@pytest.fixture(name="locals_tf_content")
def fixture_locals_tf_content(terraform_dir):
    """Provide locals.tf file content."""
    return (terraform_dir / "locals.tf").read_text()


@pytest.fixture(name="cloudwatch_tf_content")
def fixture_cloudwatch_tf_content(terraform_dir):
    """Provide cloudwatch.tf file content."""
    return (terraform_dir / "cloudwatch.tf").read_text()


@pytest.fixture(name="eventbridge_tf_content")
def fixture_eventbridge_tf_content(terraform_dir):
    """Provide eventbridge.tf file content."""
    return (terraform_dir / "eventbridge.tf").read_text()


@pytest.fixture(name="sns_tf_content")
def fixture_sns_tf_content(terraform_dir):
    """Provide sns.tf file content."""
    return (terraform_dir / "sns.tf").read_text()


@pytest.fixture(name="s3_tf_content")
def fixture_s3_tf_content(terraform_dir):
    """Provide s3.tf file content."""
    return (terraform_dir / "s3.tf").read_text()


@pytest.fixture(name="outputs_tf_content")
def fixture_outputs_tf_content(terraform_dir):
    """Provide outputs.tf file content."""
    return (terraform_dir / "outputs.tf").read_text()
