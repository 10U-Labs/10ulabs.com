from pathlib import Path

import pytest


@pytest.fixture
def module_path(modules_dir: Path) -> Path:
    return modules_dir / "s3_bucket"
