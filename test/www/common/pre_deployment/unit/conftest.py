import pytest
from repo_utils import REPO_ROOT


SRC_DIR = REPO_ROOT / "src" / "www" / "common"


@pytest.fixture
def src_dir():
    return SRC_DIR
