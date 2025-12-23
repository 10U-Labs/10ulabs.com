"""Layer 1: Existence tests for contact endpoint post-deployment.

Tests ONLY that resources exist. No configuration checks.
These tests verify that resources created by THIS workflow exist after deployment.

Three-layer testing model:
- Layer 1: Existence - Resources were created
"""

import pytest
from botocore.exceptions import ClientError


pytestmark = pytest.mark.layer(1)


class TestLambdaAndIAMExistence:
    """Layer 1: Verify Lambda function and IAM role exist."""

    def test_contact_handler_lambda_exists(self, lambda_client, shared_config):
        """Verify TenULabsContactHandler Lambda function exists."""
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "contact", "TenULabsContactHandler"
        )
        try:
            response = lambda_client.get_function(FunctionName=function_name)
            assert response["Configuration"]["FunctionName"] == function_name
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.fail(
                    f"Lambda function '{function_name}' does not exist. "
                    "Run terraform apply in src/api/endpoints/contact/"
                )
            raise

    def test_contact_handler_iam_role_exists(self, iam_client, shared_config):
        """Verify ContactHandler IAM role exists."""
        resource_prefix = shared_config.get("resource_prefix", "TenULabs")
        role_name = f"{resource_prefix}ContactHandlerServiceRole"
        try:
            response = iam_client.get_role(RoleName=role_name)
            assert response["Role"]["RoleName"] == role_name
        except iam_client.exceptions.NoSuchEntityException:
            pytest.fail(
                f"IAM role '{role_name}' does not exist. "
                "Run terraform apply in src/api/endpoints/contact/"
            )

    def test_contact_handler_log_group_exists(
        self, contact_handler_log_group
    ):
        """Verify CloudWatch log group for ContactHandler exists."""
        assert contact_handler_log_group["exists"], (
            f"CloudWatch log group '{contact_handler_log_group['name']}' "
            "does not exist"
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
                    "Run terraform apply in src/api/endpoints/contact/"
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
