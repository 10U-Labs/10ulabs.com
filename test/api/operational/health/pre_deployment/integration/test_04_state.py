from repo_utils import REPO_ROOT
from terraform_drift.test_helpers import create_orphaned_resource_tests


HEALTH_SRC = REPO_ROOT / "src" / "api" / "operational" / "health"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=HEALTH_SRC,
    region="us-east-2",
)
