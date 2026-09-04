import sys
from pathlib import Path
from typing import Any, Dict

import boto3
import pytest

_REPO_ROOT = Path(__file__).parent.parent
_LIB_DIR = _REPO_ROOT / "lib" / "python"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))


SHARED_CONFIG: Dict[str, Any] = {
    "admin_iam_user": "jdrowne",
    "api_fqdn": "api.10ulabs.com",
    "aws_region": "us-east-2",
    "domain_name": "10ulabs.com",
    "github_org": "10U-Labs",
    "id": "2436221",
    "installation_id": "98653544",
    "kms_lambda_key_arn": "arn:aws:kms:${local.aws_region}:${local.aws_account_id}:key/*",
    "name_for_central_logs_bucket": "10ulabs-central-logs-us-east-2",
    "name_for_github_repo": "10ulabs.com",
    "name_for_terraform_state_bucket": "10ulabs-terraform-state-us-east-2",
    "resource_prefix": "TenULabs",
    "ssm_github_pat_name": "/github/pat",
    "ssm_prefix": "/github/app",
    "catchall": "TenULabsCatchAllHandler",
    "contact": "TenULabsContactHandler",
    "echo": "TenULabsDiagnosticsHandler",
    "health": "TenULabsHealthHandler",
    "rack_configurations": "TenULabsRackConfigurationsHandler",
    "sessions": "TenULabsSessionsHandler",
    "lambda_handler_names": {
        "catchall": "TenULabsCatchAllHandler",
        "contact": "TenULabsContactHandler",
        "echo": "TenULabsDiagnosticsHandler",
        "health": "TenULabsHealthHandler",
        "rack_configurations": "TenULabsRackConfigurationsHandler",
        "sessions": "TenULabsSessionsHandler",
    },
}


@pytest.fixture(scope="session")
def shared_config() -> Dict[str, Any]:
    return dict(SHARED_CONFIG)


@pytest.fixture(scope="session")
def aws_region(request: pytest.FixtureRequest) -> str:
    config = request.getfixturevalue("shared_config")
    return config["aws_region"]


@pytest.fixture(scope="session")
def state_bucket_name(request: pytest.FixtureRequest) -> str:
    config = request.getfixturevalue("shared_config")
    return config["name_for_terraform_state_bucket"]


@pytest.fixture(scope="session")
def sts_client(request: pytest.FixtureRequest) -> Any:
    region = request.getfixturevalue("aws_region")
    return boto3.client("sts", region_name=region)


@pytest.fixture(scope="session")
def s3_client(request: pytest.FixtureRequest) -> Any:
    region = request.getfixturevalue("aws_region")
    return boto3.client("s3", region_name=region)
