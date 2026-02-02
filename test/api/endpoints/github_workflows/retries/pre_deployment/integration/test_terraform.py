"""Pre-deployment integration tests for retries Terraform configuration."""
from test_utils.terraform_tests import TerraformFilesExistTestMixin


class TestTerraformFilesExist(TerraformFilesExistTestMixin):
    """Tests that required Terraform files exist.

    Retries endpoint does not use EventBridge, so excludes eventbridge.tf.
    """

    REQUIRED_TF_FILES = [
        "backend.tf",
        "providers.tf",
        "shared.tf",
        "locals.tf",
        "lambda.tf",
        "iam.tf",
        "outputs.tf",
    ]
