import sys
from pathlib import Path
from typing import Any, Dict

import boto3
import pytest

from terraform_config import get_shared_config


_REPO_ROOT = Path(__file__).parent.parent
_LIB_DIR = _REPO_ROOT / "lib" / "python"
if str(_LIB_DIR) not in sys.path:
    sys.path.insert(0, str(_LIB_DIR))


@pytest.fixture(scope="session")
def shared_config() -> Dict[str, Any]:
    return get_shared_config()


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
