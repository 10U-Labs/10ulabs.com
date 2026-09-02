from pathlib import Path

import pytest
from repo_utils import REPO_ROOT

MODULES_DIR = REPO_ROOT / "lib" / "terraform"


@pytest.fixture
def modules_dir() -> Path:
    return MODULES_DIR


@pytest.fixture
def main_tf_content(module_path: Path) -> str:
    with open(module_path / "main.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def variables_tf_content(module_path: Path) -> str:
    with open(module_path / "variables.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def outputs_tf_content(module_path: Path) -> str:
    with open(module_path / "outputs.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def versions_tf_content(module_path: Path) -> str:
    with open(module_path / "versions.tf", encoding="utf-8") as f:
        return f.read()
