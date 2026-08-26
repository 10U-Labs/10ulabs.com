import pytest


@pytest.fixture(name="module_path")
def fixture_module_path(modules_dir):
    return modules_dir / "common"


@pytest.fixture
def locals_tf_content(module_path):
    with open(module_path / "locals.tf", encoding="utf-8") as f:
        return f.read()
