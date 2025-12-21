"""Layer 4: Existence tests for api_backend pre-deployment validation.

Verify prerequisite resources exist (assumes authorization passed).
"""
import pytest
from botocore.exceptions import ClientError

pytestmark = pytest.mark.dependency(
    name="layer4", depends=["layer1", "layer2", "layer3"]
)


def test_iam_role_exists(iam_client, current_role_name):
    """Verify the IAM role exists."""
    if not current_role_name:
        pytest.skip("Could not determine current role name")
    try:
        response = iam_client.get_role(RoleName=current_role_name)
        assert response["Role"]["RoleName"] == current_role_name
    except ClientError as e:
        if e.response["Error"]["Code"] == "NoSuchEntity":
            pytest.fail(
                f"IAM role '{current_role_name}' does not exist. "
                "Run terraform apply in src/bootstrap/"
            )
        raise


def test_state_bucket_exists(s3_client, state_bucket_name):
    """Verify the terraform state bucket exists."""
    try:
        response = s3_client.head_bucket(Bucket=state_bucket_name)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            pytest.fail(
                f"Terraform state bucket '{state_bucket_name}' does not exist. "
                "Run terraform apply in src/bootstrap/"
            )
        raise


def test_bootstrap_terraform_initialized(bootstrap_initialized):
    """Verify terraform init succeeds for bootstrap."""
    assert bootstrap_initialized, (
        "Terraform init failed for src/bootstrap/. "
        "Check AWS credentials and S3 backend configuration."
    )


def test_central_logs_bucket_arn_output_exists(bootstrap_outputs):
    """Verify arn_for_central_logs_bucket output exists."""
    arn = bootstrap_outputs.get("arn_for_central_logs_bucket")
    assert arn, (
        "arn_for_central_logs_bucket output not found in bootstrap. "
        "Check src/bootstrap/outputs.tf"
    )


def test_github_actions_role_arn_output_exists(bootstrap_outputs):
    """Verify arn_for_github_actions_role output exists."""
    arn = bootstrap_outputs.get("arn_for_github_actions_role")
    assert arn, (
        "arn_for_github_actions_role output not found in bootstrap. "
        "Check src/bootstrap/outputs.tf"
    )


def test_central_logs_bucket_name_extracted(central_logs_bucket_name):
    """Verify central logs bucket name was extracted from ARN."""
    assert central_logs_bucket_name, (
        "Could not extract bucket name from arn_for_central_logs_bucket. "
        "Check bootstrap outputs."
    )


def test_central_logs_bucket_exists(s3_client, central_logs_bucket_name):
    """Verify the central logs bucket exists."""
    if not central_logs_bucket_name:
        pytest.skip("central_logs_bucket_name not available")
    try:
        response = s3_client.head_bucket(Bucket=central_logs_bucket_name)
        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            pytest.fail(
                f"Central logs bucket '{central_logs_bucket_name}' does not exist. "
                "Run terraform apply in src/bootstrap/"
            )
        raise
