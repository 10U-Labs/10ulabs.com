"""Layer 1: Existence tests for contact endpoint post-deployment.

Tests ONLY that resources exist. No configuration checks.
These tests verify that resources created by THIS workflow exist after deployment.

Three-layer testing model:
- Layer 1: Existence - Resources were created
"""

import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import create_lambda_existence_tests


pytestmark = pytest.mark.layer(1)


# Use factory for Lambda/IAM existence tests
TestLambdaAndIAMExistence = create_lambda_existence_tests(
    function_name_config_key="contact_handler_function_name",
    default_function_name="TenULabsContactHandler",
    terraform_path="src/api/endpoints/contact_submissions/",
    log_group_fixture="contact_handler_log_group",
)


class TestSSMAndSESExistence:
    """Layer 1: Verify SSM parameter and SES email identity exist."""

    def test_recaptcha_secret_parameter_exists(self, ssm_client):
        """Verify reCAPTCHA secret SSM parameter exists."""
        parameter_name = "/10ulabs/contact/recaptcha-secret-key"
        try:
            ssm_client.get_parameter(Name=parameter_name, WithDecryption=False)
        except ClientError as e:
            if e.response["Error"]["Code"] == "ParameterNotFound":
                pytest.fail(
                    f"SSM parameter '{parameter_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/contact_submissions/"
                )
            raise

    def test_contact_email_identity_exists(self, ses_client, shared_config):
        """Verify contact@domain SES email identity exists."""
        domain_name = shared_config.get("domain_name", "10ulabs.com")
        contact_email = f"contact@{domain_name}"
        response = ses_client.list_identities(IdentityType="EmailAddress")
        identities = response.get("Identities", [])
        assert contact_email in identities, (
            f"SES email identity '{contact_email}' does not exist. "
            f"Available identities: {identities}"
        )
