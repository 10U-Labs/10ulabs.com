from typing import Any, Dict

import pytest
from repo_utils import REPO_ROOT
from test_fixtures.config import create_simple_config


HEALTH_SRC = REPO_ROOT / "src" / "api" / "operational" / "health"


@pytest.fixture(scope="module")
def config(shared_config: Dict[str, Any]) -> Dict[str, str]:
    return create_simple_config(HEALTH_SRC / "terraform.tfvars", shared_config)
