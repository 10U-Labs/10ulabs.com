from repo_utils import REPO_ROOT
from terraform_config import TEST_AWS_REGION
from terraform_drift.test_helpers import create_orphaned_resource_tests


SESSIONS_SRC_PATH = REPO_ROOT / "src" / "api" / "endpoints" / "sessions"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=SESSIONS_SRC_PATH,
    region=TEST_AWS_REGION,
)
