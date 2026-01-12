"""Pytest fixtures for drift_recoveries Terraform unit tests."""

import pytest

from repo_utils import REPO_ROOT

TERRAFORM_DIR = (
    REPO_ROOT / "src" / "api" / "endpoints" / "drift_recoveries"
)


@pytest.fixture(name="terraform_dir")
def fixture_terraform_dir():
    """Provide path to drift_recoveries Terraform directory."""
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


@pytest.fixture(name="sns_tf_content")
def fixture_sns_tf_content(terraform_dir):
    """Provide sns.tf file content."""
    return (terraform_dir / "sns.tf").read_text()


@pytest.fixture(name="eventbridge_tf_content")
def fixture_eventbridge_tf_content(terraform_dir):
    """Provide eventbridge.tf file content."""
    return (terraform_dir / "eventbridge.tf").read_text()


@pytest.fixture(name="config_tf_content")
def fixture_config_tf_content(terraform_dir):
    """Provide config.tf file content."""
    return (terraform_dir / "config.tf").read_text()


@pytest.fixture(name="locals_tf_content")
def fixture_locals_tf_content(terraform_dir):
    """Provide locals.tf file content."""
    return (terraform_dir / "locals.tf").read_text()


@pytest.fixture(name="outputs_tf_content")
def fixture_outputs_tf_content(terraform_dir):
    """Provide outputs.tf file content."""
    return (terraform_dir / "outputs.tf").read_text()
