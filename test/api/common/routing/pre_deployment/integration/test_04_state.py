from repo_utils import REPO_ROOT
from terraform_drift.test_helpers import create_orphaned_resource_tests


API_BACKEND_SRC = REPO_ROOT / "src" / "api" / "common" / "routing"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=API_BACKEND_SRC,
    region="us-east-2",
)
