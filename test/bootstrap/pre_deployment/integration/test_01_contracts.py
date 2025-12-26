"""Layer 1: Contract tests for bootstrap pre-deployment validation.

Verify cross-file compatibility between Terraform configuration files. No AWS calls.
"""
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.layer(1)


def _get_project_root() -> Path:
    """Find the project root by traversing up from the test file."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / "src").exists() and (current / "test").exists():
            return current
        current = current.parent
    raise RuntimeError("Could not find project root")


def _extract_module_shared_refs(content: str) -> set[str]:
    """Extract all module.shared.* references from Terraform content."""
    pattern = r"module\.shared\.([a-zA-Z_][a-zA-Z0-9_]*)"
    return set(re.findall(pattern, content))


def _extract_output_names(outputs_content: str) -> set[str]:
    """Extract output names from Terraform outputs.tf content."""
    pattern = r'output\s+"([a-zA-Z_][a-zA-Z0-9_]*)"\s*\{'
    return set(re.findall(pattern, outputs_content))


def _extract_module_refs(content: str, module_name: str) -> set[str]:
    """Extract module.<name>.* references from Terraform content."""
    pattern = rf"module\.{module_name}\.([a-zA-Z_][a-zA-Z0-9_]*)"
    return set(re.findall(pattern, content))


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return _get_project_root()


@pytest.fixture
def bootstrap_dir(project_root: Path) -> Path:
    """Get the bootstrap source directory."""
    return project_root / "src" / "bootstrap"


@pytest.fixture
def shared_module_dir(project_root: Path) -> Path:
    """Get the shared module directory."""
    return project_root / "lib" / "terraform" / "modules" / "shared"


@pytest.fixture
def locals_content(bootstrap_dir: Path) -> str:
    """Read locals.tf content."""
    return (bootstrap_dir / "locals.tf").read_text()


@pytest.fixture
def outputs_content(bootstrap_dir: Path) -> str:
    """Read outputs.tf content."""
    return (bootstrap_dir / "outputs.tf").read_text()


@pytest.fixture
def shared_outputs(shared_module_dir: Path) -> set[str]:
    """Get output names from shared module."""
    content = (shared_module_dir / "outputs.tf").read_text()
    return _extract_output_names(content)


@pytest.fixture
def github_oidc_outputs(bootstrap_dir: Path) -> set[str]:
    """Get output names from github_oidc module."""
    content = (bootstrap_dir / "modules" / "github_oidc" / "outputs.tf").read_text()
    return _extract_output_names(content)


@pytest.fixture
def domain_outputs(bootstrap_dir: Path) -> set[str]:
    """Get output names from domain module."""
    content = (bootstrap_dir / "modules" / "domain" / "outputs.tf").read_text()
    return _extract_output_names(content)


@pytest.fixture
def central_logs_outputs(bootstrap_dir: Path) -> set[str]:
    """Get output names from central_logs module."""
    content = (bootstrap_dir / "modules" / "central_logs" / "outputs.tf").read_text()
    return _extract_output_names(content)


@pytest.fixture
def cloudtrail_outputs(bootstrap_dir: Path) -> set[str]:
    """Get output names from cloudtrail module."""
    content = (bootstrap_dir / "modules" / "cloudtrail" / "outputs.tf").read_text()
    return _extract_output_names(content)


def test_locals_tf_exists(bootstrap_dir: Path):
    """Verify locals.tf file exists."""
    path = bootstrap_dir / "locals.tf"
    assert path.exists(), f"locals.tf not found at {path}"


def test_outputs_tf_exists(bootstrap_dir: Path):
    """Verify outputs.tf file exists."""
    path = bootstrap_dir / "outputs.tf"
    assert path.exists(), f"outputs.tf not found at {path}"


def test_shared_module_outputs_tf_exists(shared_module_dir: Path):
    """Verify shared module outputs.tf file exists."""
    path = shared_module_dir / "outputs.tf"
    assert path.exists(), f"shared module outputs.tf not found at {path}"


def test_locals_shared_refs_exist_in_shared_module(
    locals_content: str, shared_outputs: set[str]
):
    """Verify all module.shared.* references in locals.tf exist in shared module."""
    shared_refs = _extract_module_shared_refs(locals_content)

    missing = shared_refs - shared_outputs
    assert not missing, (
        f"module.shared.* references in locals.tf are missing from shared module:\n"
        f"  Missing: {sorted(missing)}\n"
        f"  locals.tf references: {sorted(shared_refs)}\n"
        f"  shared module provides: {sorted(shared_outputs)}"
    )


def test_outputs_github_oidc_refs_exist_in_module(
    outputs_content: str, github_oidc_outputs: set[str]
):
    """Verify all module.github_oidc.* references in outputs.tf exist in module."""
    refs = _extract_module_refs(outputs_content, "github_oidc")

    missing = refs - github_oidc_outputs
    assert not missing, (
        f"module.github_oidc.* references in outputs.tf missing from module:\n"
        f"  Missing: {sorted(missing)}\n"
        f"  outputs.tf references: {sorted(refs)}\n"
        f"  github_oidc module provides: {sorted(github_oidc_outputs)}"
    )


def test_outputs_domain_refs_exist_in_module(
    outputs_content: str, domain_outputs: set[str]
):
    """Verify all module.domain.* references in outputs.tf exist in module."""
    refs = _extract_module_refs(outputs_content, "domain")

    missing = refs - domain_outputs
    assert not missing, (
        f"module.domain.* references in outputs.tf missing from module:\n"
        f"  Missing: {sorted(missing)}\n"
        f"  outputs.tf references: {sorted(refs)}\n"
        f"  domain module provides: {sorted(domain_outputs)}"
    )


def test_outputs_central_logs_refs_exist_in_module(
    outputs_content: str, central_logs_outputs: set[str]
):
    """Verify all module.central_logs.* references in outputs.tf exist in module."""
    refs = _extract_module_refs(outputs_content, "central_logs")

    missing = refs - central_logs_outputs
    assert not missing, (
        f"module.central_logs.* references in outputs.tf missing from module:\n"
        f"  Missing: {sorted(missing)}\n"
        f"  outputs.tf references: {sorted(refs)}\n"
        f"  central_logs module provides: {sorted(central_logs_outputs)}"
    )


def test_outputs_cloudtrail_refs_exist_in_module(
    outputs_content: str, cloudtrail_outputs: set[str]
):
    """Verify all module.cloudtrail.* references in outputs.tf exist in module."""
    refs = _extract_module_refs(outputs_content, "cloudtrail")

    missing = refs - cloudtrail_outputs
    assert not missing, (
        f"module.cloudtrail.* references in outputs.tf missing from module:\n"
        f"  Missing: {sorted(missing)}\n"
        f"  outputs.tf references: {sorted(refs)}\n"
        f"  cloudtrail module provides: {sorted(cloudtrail_outputs)}"
    )


def test_variables_tf_exists(bootstrap_dir: Path):
    """Verify variables.tf file exists."""
    path = bootstrap_dir / "variables.tf"
    assert path.exists(), f"variables.tf not found at {path}"


def test_terraform_tfvars_exists(bootstrap_dir: Path):
    """Verify terraform.tfvars file exists."""
    path = bootstrap_dir / "terraform.tfvars"
    assert path.exists(), f"terraform.tfvars not found at {path}"
