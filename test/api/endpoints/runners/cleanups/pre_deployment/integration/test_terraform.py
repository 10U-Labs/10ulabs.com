"""Pre-deployment integration tests for runners cleanup Terraform config."""
from test_utils.terraform_tests import TerraformFilesExistTestMixin


class TestTerraformFilesExist(TerraformFilesExistTestMixin):
    """Tests that required Terraform files exist.

    Uses DEFAULT_TERRAFORM_FILES which includes eventbridge.tf.
    """
