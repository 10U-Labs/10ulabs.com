from test_fixtures.integration import (
    create_lambda_api_gateway_wiring_tests,
    create_lambda_iam_wiring_tests,
)


TestLambdaWiring = create_lambda_api_gateway_wiring_tests(
    function_name_config_key="contact_handler_function_name",
    default_function_name="TenULabsContactHandler",
)


TestIAMPolicyWiring = create_lambda_iam_wiring_tests(
    function_name_config_key="contact_handler_function_name",
    default_function_name="TenULabsContactHandler",
    check_basic_execution=True,
    check_lambda_trust=True,
)


class TestContactHandlerInlinePolicies:
    def test_contact_handler_role_has_ssm_policy(self, iam_client, config):
        resource_prefix = config.get("resource_prefix", "TenULabs")
        role_name = f"{resource_prefix}ContactHandlerServiceRole"
        response = iam_client.list_role_policies(RoleName=role_name)
        inline_policies = response.get("PolicyNames", [])
        assert "SSMParameterAccess" in inline_policies, (
            f"IAM role '{role_name}' missing SSMParameterAccess inline policy. "
            f"Available policies: {inline_policies}"
        )

    def test_contact_handler_role_has_kms_policy(self, iam_client, config):
        resource_prefix = config.get("resource_prefix", "TenULabs")
        role_name = f"{resource_prefix}ContactHandlerServiceRole"
        response = iam_client.list_role_policies(RoleName=role_name)
        inline_policies = response.get("PolicyNames", [])
        assert "KMSDecrypt" in inline_policies, (
            f"IAM role '{role_name}' missing KMSDecrypt inline policy. "
            f"Available policies: {inline_policies}"
        )

    def test_contact_handler_role_has_ses_policy(self, iam_client, config):
        resource_prefix = config.get("resource_prefix", "TenULabs")
        role_name = f"{resource_prefix}ContactHandlerServiceRole"
        response = iam_client.list_role_policies(RoleName=role_name)
        inline_policies = response.get("PolicyNames", [])
        assert "SESAccess" in inline_policies, (
            f"IAM role '{role_name}' missing SESAccess inline policy. "
            f"Available policies: {inline_policies}"
        )
