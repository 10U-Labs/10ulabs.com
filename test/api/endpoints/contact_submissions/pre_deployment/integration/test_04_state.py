from repo_utils import REPO_ROOT
from terraform_drift.test_helpers import create_orphaned_resource_tests


CONTACT_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "contact_submissions"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=CONTACT_SRC,
    region="us-east-2",
)
