import re

import pytest

from repo_utils import REPO_ROOT
from test_fixtures.terraform import terraform_init, terraform_output


BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"


@pytest.fixture(scope="session", name="bootstrap_initialized")
def bootstrap_initialized_fixture():
    return terraform_init(BOOTSTRAP_DIR)


@pytest.fixture(scope="session", name="bootstrap_outputs")
def bootstrap_outputs_fixture(bootstrap_initialized):
    if not bootstrap_initialized:
        pytest.skip("Terraform init failed for bootstrap")
    return {
        "arn_for_central_logs_bucket": terraform_output(
            BOOTSTRAP_DIR, "arn_for_central_logs_bucket"
        ),
        "arn_for_github_actions_role": terraform_output(
            BOOTSTRAP_DIR, "arn_for_github_actions_role"
        ),
        "arn_for_state_bucket": terraform_output(
            BOOTSTRAP_DIR, "arn_for_state_bucket"
        ),
    }


@pytest.fixture(scope="session")
def central_logs_bucket_name(bootstrap_outputs):
    arn = bootstrap_outputs.get("arn_for_central_logs_bucket", "")
    if not arn:
        return ""
    match = re.match(r"arn:aws:s3:::(.+)$", arn)
    return match.group(1) if match else ""
