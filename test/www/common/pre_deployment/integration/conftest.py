import boto3
import pytest
from repo_utils import REPO_ROOT
from terraform_config import TEST_AWS_REGION
from test_fixtures.terraform import terraform_init, terraform_output


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "layer(num): mark test as belonging to layer N"
    )


BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"


def _get_bootstrap_outputs() -> dict:
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
    return TEST_AWS_REGION


@pytest.fixture(scope="session")
def s3_client():
    return boto3.client("s3", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def iam_client():
    return boto3.client("iam", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def route53_client():
    return boto3.client("route53", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def sts_client():
    return boto3.client("sts", region_name=TEST_AWS_REGION)


@pytest.fixture(scope="session")
def bootstrap_outputs():
    outputs = _get_bootstrap_outputs()
    if not outputs:
        pytest.skip("Terraform init failed for bootstrap")
    return outputs


@pytest.fixture(scope="session")
def state_bucket_name(request):
    outputs = request.getfixturevalue("bootstrap_outputs")
    arn = outputs.get("state_bucket_arn", "")
    if not arn:
        pytest.skip("state_bucket_arn not found in bootstrap outputs")
    return arn.split(":")[-1]


@pytest.fixture(scope="session")
def github_actions_role_arn(request):
    outputs = request.getfixturevalue("bootstrap_outputs")
    arn = outputs.get("github_actions_role_arn", "")
    if not arn:
        pytest.skip("github_actions_role_arn not found in bootstrap outputs")
    return arn


@pytest.fixture(scope="session")
def github_actions_role_name(request):
    outputs = request.getfixturevalue("bootstrap_outputs")
    name = outputs.get("github_actions_role_name", "")
    if not name:
        pytest.skip("github_actions_role_name not found in bootstrap outputs")
    return name


@pytest.fixture(scope="session")
def hosted_zone_id(request):
    outputs = request.getfixturevalue("bootstrap_outputs")
    zone_id = outputs.get("hosted_zone_id", "")
    if not zone_id:
        pytest.skip("hosted_zone_id not found in bootstrap outputs")
    return zone_id


@pytest.fixture(scope="session")
def current_identity(request):
    client = request.getfixturevalue("sts_client")
    return client.get_caller_identity()
