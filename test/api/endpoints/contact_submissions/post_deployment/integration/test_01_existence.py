from typing import Any, Dict

import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import create_lambda_existence_tests


TestLambdaAndIAMExistence = create_lambda_existence_tests(
    function_name_config_key="contact_handler_function_name",
    default_function_name="TenULabsContactHandler",
    terraform_path="src/api/endpoints/contact_submissions/",
    log_group_fixture="contact_handler_log_group",
)


class TestSSMAndSESExistence:
    def test_recaptcha_secret_parameter_exists(self, ssm_client: Any) -> None:
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
        assert True

    def test_contact_email_identity_exists(
        self,
        ses_client: Any,
        shared_config: Dict[str, Any]
    ) -> None:
        domain_name = shared_config.get("domain_name", "10ulabs.com")
        contact_email = f"contact@{domain_name}"
        response = ses_client.list_identities(IdentityType="EmailAddress")
        identities = response.get("Identities", [])
        assert contact_email in identities, (
            f"SES email identity '{contact_email}' does not exist. "
            f"Available identities: {identities}"
        )
