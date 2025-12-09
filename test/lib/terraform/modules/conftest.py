"""Shared fixtures and utilities for Terraform module tests."""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
MODULES_DIR = REPO_ROOT / "lib" / "terraform" / "modules"


@pytest.fixture(name="modules_dir")
def fixture_modules_dir():
    """Provide path to Terraform modules directory."""
    return MODULES_DIR


@pytest.fixture(name="main_tf_content")
def fixture_main_tf_content(module_path):
    """Provide main.tf file content."""
    with open(module_path / "main.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(name="variables_tf_content")
def fixture_variables_tf_content(module_path):
    """Provide variables.tf file content."""
    with open(module_path / "variables.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(name="outputs_tf_content")
def fixture_outputs_tf_content(module_path):
    """Provide outputs.tf file content."""
    with open(module_path / "outputs.tf", encoding="utf-8") as f:
        return f.read()
