"""Layer 4: State validation tests for runners endpoint pre-deployment.

Verifies Terraform state matches AWS reality. Skips in cold state (no prior state).
"""
import pytest

from repo_utils import REPO_ROOT
from terraform_drift.test_helpers import create_orphaned_resource_tests


RUNNERS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=RUNNERS_SRC,
    region="us-east-2",
)
