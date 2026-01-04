"""Layer 3: State tests for contact endpoint pre-deployment.

Tests that Terraform state matches AWS reality. Resources Terraform plans
to create should not already exist in AWS.

Six-layer testing model:
- Layer 3: State - Terraform state matches AWS reality
"""
import pytest

from repo_utils import REPO_ROOT
from terraform_drift.test_helpers import create_orphaned_resource_tests




CONTACT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "contact_submissions"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=CONTACT_SRC,
    region="us-east-2",
)
