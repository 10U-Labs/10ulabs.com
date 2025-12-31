"""Pre-deployment fixtures for api/common/parameters tests."""
from pathlib import Path

from repo_utils import REPO_ROOT
from test_fixtures.terraform import terraform_init, terraform_output

import pytest

PARAMETERS_SRC = REPO_ROOT / "src" / "api" / "shared" / "parameters"
NETWORKING_SRC = REPO_ROOT / "src" / "api" / "shared" / "networking"


@pytest.fixture(scope="session")
def parameters_src_dir() -> Path:
    """Return path to the parameters source directory."""
    return PARAMETERS_SRC


@pytest.fixture(scope="session")
def networking_terraform_initialized():
    """Initialize terraform for networking state access."""
    return terraform_init(NETWORKING_SRC)


@pytest.fixture(scope="session")
def networking_outputs(request):
    """Get networking terraform outputs (prerequisite for parameters module)."""
    if not request.getfixturevalue("networking_terraform_initialized"):
        pytest.skip("Terraform init failed for networking")
    return {
        "vpc_id": terraform_output(NETWORKING_SRC, "vpc_id"),
        "public_subnets_ids": terraform_output(NETWORKING_SRC, "public_subnets_ids"),
        "security_group_id_for_runners": terraform_output(
            NETWORKING_SRC, "security_group_id_for_runners"
        ),
    }
