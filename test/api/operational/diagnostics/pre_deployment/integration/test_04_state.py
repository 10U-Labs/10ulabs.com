from repo_utils import REPO_ROOT
from terraform_drift.test_helpers import create_orphaned_resource_tests


DIAGNOSTICS_SRC = REPO_ROOT / "src" / "api" / "operational" / "diagnostics"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=DIAGNOSTICS_SRC,
    region="us-east-2",
)
