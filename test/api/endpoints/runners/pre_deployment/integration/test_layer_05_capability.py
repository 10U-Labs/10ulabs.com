"""Layer 5: Capability - Can we perform required operations?

These tests verify that we can perform the operations required for deployment,
such as detecting Terraform state drift.

Five-layer testing model:
- Layer 1: Authentication - Are credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: Existence - Do the required resources exist?
- Layer 4: Configuration - Are resources configured correctly?
- Layer 5: Capability - Can we perform required operations? (THIS FILE)
"""
from pathlib import Path

from terraform_drift.test_helpers import create_orphaned_resource_tests


RUNNERS_SRC = (
    Path(__file__).parents[6] / "src" / "api" / "endpoints" / "runners"
)


TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=RUNNERS_SRC,
    region="us-east-2",
)
