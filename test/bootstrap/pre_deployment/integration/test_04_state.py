from repo_utils import REPO_ROOT
from terraform_config import TEST_AWS_REGION
from terraform_drift.test_helpers import create_orphaned_resource_tests


BOOTSTRAP_DIR = REPO_ROOT / "src" / "bootstrap"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=BOOTSTRAP_DIR,
    region=TEST_AWS_REGION,
    require_existing_state=True,
)
