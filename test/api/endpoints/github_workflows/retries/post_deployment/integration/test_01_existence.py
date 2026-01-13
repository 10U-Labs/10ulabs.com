"""Post-deployment integration tests verifying AWS resources exist."""
from test_utils.existence_tests import AwsResourceExistsTestMixin


class TestAwsResourcesExist(AwsResourceExistsTestMixin):
    """Tests that AWS resources exist."""
