from repo_utils import REPO_ROOT
from terraform_config import TEST_AWS_REGION
from terraform_drift.test_helpers import create_orphaned_resource_tests


WWW_SHARED_SRC = REPO_ROOT / "src" / "www" / "common"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=WWW_SHARED_SRC,
    region=TEST_AWS_REGION,
)
