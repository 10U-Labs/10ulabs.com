"""Pytest fixtures for pre-deployment integration tests."""
import boto3
import pytest
from repo_utils import REPO_ROOT
from test_fixtures.terraform import terraform_init, terraform_output

pytest_plugins = ['pytest_layers']


BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"
AWS_REGION_VALUE = "us-east-2"


def _get_bootstrap_outputs() -> dict:
    """Get all bootstrap terraform outputs."""
    if not terraform_init(BOOTSTRAP_DIR):
        return {}
    return {
        "state_bucket_arn": terraform_output(
            BOOTSTRAP_DIR, "arn_for_state_bucket"
        ),
        "github_actions_role_arn": terraform_output(
            BOOTSTRAP_DIR, "arn_for_github_actions_role"
        ),
        "github_actions_role_name": terraform_output(
            BOOTSTRAP_DIR, "name_for_github_actions_role"
        ),
        "hosted_zone_id": terraform_output(
            BOOTSTRAP_DIR, "hosted_zone_id"
        ),
    }


@pytest.fixture(scope="session")
def aws_region():
    """Provide the AWS region."""
    return AWS_REGION_VALUE


@pytest.fixture(scope="session")
def s3_client():
    """Create an S3 client."""
    return boto3.client("s3", region_name=AWS_REGION_VALUE)


@pytest.fixture(scope="session")
def iam_client():
    """Create an IAM client."""
    return boto3.client("iam", region_name=AWS_REGION_VALUE)


@pytest.fixture(scope="session")
def route53_client():
    """Create a Route53 client."""
    return boto3.client("route53", region_name=AWS_REGION_VALUE)


@pytest.fixture(scope="session")
def sts_client():
    """Create an STS client."""
    return boto3.client("sts", region_name=AWS_REGION_VALUE)


@pytest.fixture(scope="session")
def bootstrap_outputs():
    """Get bootstrap terraform outputs."""
    outputs = _get_bootstrap_outputs()
    if not outputs:
        pytest.skip("Terraform init failed for bootstrap")
    return outputs


@pytest.fixture(scope="session")
def state_bucket_name(request):
    """Extract state bucket name from ARN."""
    outputs = request.getfixturevalue("bootstrap_outputs")
    arn = outputs.get("state_bucket_arn", "")
    if not arn:
        pytest.skip("state_bucket_arn not found in bootstrap outputs")
    return arn.split(":")[-1]


@pytest.fixture(scope="session")
def github_actions_role_arn(request):
    """Get GitHub Actions role ARN."""
    outputs = request.getfixturevalue("bootstrap_outputs")
    arn = outputs.get("github_actions_role_arn", "")
    if not arn:
        pytest.skip("github_actions_role_arn not found in bootstrap outputs")
    return arn


@pytest.fixture(scope="session")
def github_actions_role_name(request):
    """Get GitHub Actions role name."""
    outputs = request.getfixturevalue("bootstrap_outputs")
    name = outputs.get("github_actions_role_name", "")
    if not name:
        pytest.skip("github_actions_role_name not found in bootstrap outputs")
    return name


@pytest.fixture(scope="session")
def hosted_zone_id(request):
    """Get Route53 hosted zone ID."""
    outputs = request.getfixturevalue("bootstrap_outputs")
    zone_id = outputs.get("hosted_zone_id", "")
    if not zone_id:
        pytest.skip("hosted_zone_id not found in bootstrap outputs")
    return zone_id


@pytest.fixture(scope="session")
def current_identity(request):
    """Get the current AWS identity."""
    client = request.getfixturevalue("sts_client")
    return client.get_caller_identity()
