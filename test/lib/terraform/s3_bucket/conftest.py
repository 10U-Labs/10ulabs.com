import pytest


@pytest.fixture
def module_path(modules_dir):
    return modules_dir / "s3_bucket"
