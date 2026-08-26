import re
from pathlib import Path

import pytest

from repo_utils import REPO_ROOT


def _extract_output_names(outputs_content: str) -> set[str]:
    pattern = r'output\s+"([a-zA-Z_][a-zA-Z0-9_]*)"\s*\{'
    return set(re.findall(pattern, outputs_content))


@pytest.fixture(name="bootstrap_dir")
def bootstrap_dir_fixture() -> Path:
    return REPO_ROOT / "src" / "bootstrap"


@pytest.fixture(name="common_module_dir")
def common_module_dir_fixture() -> Path:
    return REPO_ROOT / "lib" / "terraform" / "common"


@pytest.fixture
def locals_content(bootstrap_dir: Path) -> str:
    return (bootstrap_dir / "locals.tf").read_text()


@pytest.fixture(name="outputs_content")
def outputs_content_fixture(bootstrap_dir: Path) -> str:
    return (bootstrap_dir / "outputs.tf").read_text()


@pytest.fixture
def common_outputs(common_module_dir: Path) -> set[str]:
    content = (common_module_dir / "outputs.tf").read_text()
    return _extract_output_names(content)


@pytest.fixture
def github_oidc_outputs(bootstrap_dir: Path) -> set[str]:
    content = (bootstrap_dir / "modules" / "github_oidc" / "outputs.tf").read_text()
    return _extract_output_names(content)


@pytest.fixture
def domain_outputs(bootstrap_dir: Path) -> set[str]:
    content = (bootstrap_dir / "modules" / "domain" / "outputs.tf").read_text()
    return _extract_output_names(content)


@pytest.fixture
def central_logs_outputs(bootstrap_dir: Path) -> set[str]:
    content = (bootstrap_dir / "modules" / "central_logs" / "outputs.tf").read_text()
    return _extract_output_names(content)


@pytest.fixture
def cloudtrail_outputs(bootstrap_dir: Path) -> set[str]:
    content = (bootstrap_dir / "modules" / "cloudtrail" / "outputs.tf").read_text()
    return _extract_output_names(content)
