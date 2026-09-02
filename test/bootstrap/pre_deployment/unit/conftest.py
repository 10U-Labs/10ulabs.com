from typing import Any

import pytest
from test_fixtures.hcl import V7_COMPATIBLE


@pytest.fixture(scope="session")
def v7_compatible() -> Any:
    return V7_COMPATIBLE
