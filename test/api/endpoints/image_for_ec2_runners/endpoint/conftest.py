from typing import Any, Dict

import pytest

from .helpers import get_aws_region, get_github_repo


@pytest.fixture(scope="module")
def aws_region() -> str:
    return get_aws_region()


@pytest.fixture(scope="module")
def github_repo() -> str:
    return get_github_repo()


@pytest.fixture(scope="module")
def config() -> Dict[str, Any]:
    return {
        'aws_region': get_aws_region(),
        'github_repo': get_github_repo(),
    }
