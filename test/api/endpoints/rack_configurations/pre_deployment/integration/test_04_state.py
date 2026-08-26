from repo_utils import REPO_ROOT
from terraform_drift.test_helpers import create_orphaned_resource_tests


RACK_CONFIGURATIONS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "rack_configurations"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=RACK_CONFIGURATIONS_SRC,
    region="us-east-2",
)
