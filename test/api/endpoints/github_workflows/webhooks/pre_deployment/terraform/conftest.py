"""Pytest fixtures for github_workflows/webhooks Terraform unit tests."""

import pytest

from repo_utils import REPO_ROOT
from test_fixtures.terraform import create_tf_content_fixture

TERRAFORM_DIR = (
    REPO_ROOT / "src" / "api" / "endpoints" / "github_workflows" / "webhooks"
)


@pytest.fixture(name="terraform_dir")
def fixture_terraform_dir():
    """Provide path to github_workflows/webhooks Terraform directory."""
    return TERRAFORM_DIR


# Generate terraform file content fixtures using factory
fixture_lambda_tf = create_tf_content_fixture("lambda.tf")
fixture_iam_tf = create_tf_content_fixture("iam.tf")
fixture_sqs_tf = create_tf_content_fixture("sqs.tf")
fixture_dynamodb_tf = create_tf_content_fixture("dynamodb.tf")
fixture_locals_tf = create_tf_content_fixture("locals.tf")
fixture_cloudwatch_tf = create_tf_content_fixture("cloudwatch.tf")
fixture_eventbridge_tf = create_tf_content_fixture("eventbridge.tf")
fixture_sns_tf = create_tf_content_fixture("sns.tf")
fixture_s3_tf = create_tf_content_fixture("s3.tf")
fixture_outputs_tf = create_tf_content_fixture("outputs.tf")
