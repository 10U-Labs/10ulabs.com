"""Pytest fixtures for bootstrap pre-deployment integration tests.

Bootstrap Pre-Deployment Layers:
- Layer 1: Contracts (test_01_contracts.py) - Cross-file compatibility, no AWS calls
- Layer 2: Authentication (test_01_authentication.py) - AWS credentials valid
- Layer 3: Authorization (test_02_authorization.py) - Permission to inspect state bucket
- Layer 4: State (test_03_state.py) - Terraform state matches AWS reality

Layers 5-7 Exception:
Bootstrap is self-bootstrapping - it creates its own prerequisites. Layers 5-7
(Existence, Configuration, Capability) test prerequisite resources created by
OTHER workflows, which don't exist for bootstrap. Therefore, these layers are
not applicable here.
"""
import re
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT

pytest_plugins = ['test_fixtures.aws']


def _extract_output_names(outputs_content: str) -> set[str]:
    """Extract output names from Terraform outputs.tf content."""
    pattern = r'output\s+"([a-zA-Z_][a-zA-Z0-9_]*)"\s*\{'
    return set(re.findall(pattern, outputs_content))


@pytest.fixture(name="bootstrap_dir")
def bootstrap_dir_fixture() -> Path:
    """Get the bootstrap source directory."""
    return REPO_ROOT / "src" / "bootstrap"


@pytest.fixture(name="shared_module_dir")
def shared_module_dir_fixture() -> Path:
    """Get the shared module directory."""
    return REPO_ROOT / "lib" / "terraform" / "modules" / "shared"


@pytest.fixture(name="locals_content")
def locals_content_fixture(bootstrap_dir: Path) -> str:
    """Read locals.tf content."""
    return (bootstrap_dir / "locals.tf").read_text()


@pytest.fixture(name="outputs_content")
def outputs_content_fixture(bootstrap_dir: Path) -> str:
    """Read outputs.tf content."""
    return (bootstrap_dir / "outputs.tf").read_text()


@pytest.fixture(name="shared_outputs")
def shared_outputs_fixture(shared_module_dir: Path) -> set[str]:
    """Get output names from shared module."""
    content = (shared_module_dir / "outputs.tf").read_text()
    return _extract_output_names(content)


@pytest.fixture(name="github_oidc_outputs")
def github_oidc_outputs_fixture(bootstrap_dir: Path) -> set[str]:
    """Get output names from github_oidc module."""
    content = (bootstrap_dir / "modules" / "github_oidc" / "outputs.tf").read_text()
    return _extract_output_names(content)


@pytest.fixture(name="domain_outputs")
def domain_outputs_fixture(bootstrap_dir: Path) -> set[str]:
    """Get output names from domain module."""
    content = (bootstrap_dir / "modules" / "domain" / "outputs.tf").read_text()
    return _extract_output_names(content)


@pytest.fixture(name="central_logs_outputs")
def central_logs_outputs_fixture(bootstrap_dir: Path) -> set[str]:
    """Get output names from central_logs module."""
    content = (bootstrap_dir / "modules" / "central_logs" / "outputs.tf").read_text()
    return _extract_output_names(content)


@pytest.fixture(name="cloudtrail_outputs")
def cloudtrail_outputs_fixture(bootstrap_dir: Path) -> set[str]:
    """Get output names from cloudtrail module."""
    content = (bootstrap_dir / "modules" / "cloudtrail" / "outputs.tf").read_text()
    return _extract_output_names(content)
