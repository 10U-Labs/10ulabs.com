from pathlib import Path

import pytest


@pytest.fixture(name="module_path")
def fixture_module_path(modules_dir: Path) -> Path:
    return modules_dir / "common"


@pytest.fixture
def locals_tf_content(module_path: Path) -> str:
    with open(module_path / "locals.tf", encoding="utf-8") as f:
        return f.read()
