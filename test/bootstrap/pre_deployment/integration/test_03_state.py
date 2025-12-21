"""Layer 3: State validation tests for bootstrap pre-deployment.

Verifies Terraform state matches AWS reality. Skips in cold state (no prior state).
"""
import subprocess

import pytest

from repo_utils import REPO_ROOT
from terraform_config import TEST_AWS_REGION
from terraform_drift import check_resource_exists, get_planned_creates

pytestmark = pytest.mark.dependency(name="layer3", depends=["layer1", "layer2"])

BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"


def _has_existing_state() -> bool:
    """Check if bootstrap terraform has existing state."""
    result = subprocess.run(
        ["terraform", "state", "list"],
        cwd=BOOTSTRAP_DIR,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return result.returncode == 0 and len(result.stdout.strip()) > 0


def _is_terraform_initialized() -> bool:
    """Check if terraform is initialized."""
    return (BOOTSTRAP_DIR / ".terraform.lock.hcl").exists()


@pytest.mark.skipif(
    not _is_terraform_initialized(),
    reason="Terraform not initialized"
)
@pytest.mark.skipif(
    not _has_existing_state(),
    reason="Cold state - no prior Terraform state to validate against"
)
def test_no_orphaned_resources():
    """Verify no resources to be created already exist in AWS.

    This test runs terraform plan to find resources that will be created,
    then checks if any of them already exist in AWS. If they do, it means
    the resource was created outside of Terraform and needs to be imported.
    """
    creates = get_planned_creates(BOOTSTRAP_DIR)

    if not creates:
        return  # Nothing to check

    orphaned = []
    for resource in creates:
        if check_resource_exists(resource["type"], resource["name"], TEST_AWS_REGION):
            orphaned.append(resource)

    if orphaned:
        msg = "\nOrphaned resources detected:\n"
        for r in orphaned:
            msg += f"  - {r['type']}: {r['name']}\n"
            msg += f"    Fix: terraform import {r['address']} {r['name']}\n"
        pytest.fail(msg)
