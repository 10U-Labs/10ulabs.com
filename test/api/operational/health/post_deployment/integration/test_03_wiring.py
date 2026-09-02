from typing import Any, Dict

from test_fixtures.integration import (
    create_lambda_api_gateway_wiring_tests,
    create_lambda_iam_wiring_tests,
)


TestLambdaWiring = create_lambda_api_gateway_wiring_tests(
    function_name_config_key='health_handler_function_name',
    default_function_name='TenULabsHealthHandler',
)

TestIAMPolicyWiring = create_lambda_iam_wiring_tests(
    function_name_config_key='health_handler_function_name',
    default_function_name='TenULabsHealthHandler',
    check_basic_execution=True,
    check_lambda_trust=False,
)


class TestHealthSpecificIAMWiring:
    def test_health_handler_role_has_kms_inline_policy(
        self,
        iam_client: Any,
        config: Dict[str, Any]
    ) -> None:
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        role_name = f"{function_name}ServiceRole"
        response = iam_client.list_role_policies(RoleName=role_name)
        inline_policies = response.get("PolicyNames", [])
        assert "KMSDecryptPermissions" in inline_policies, (
            f"IAM role '{role_name}' missing 'KMSDecryptPermissions' inline policy. "
            f"Found policies: {inline_policies}"
        )

    def test_health_handler_role_has_lambda_trust_relationship(
        self,
        iam_client: Any,
        config: Dict[str, Any]
    ) -> None:
        function_name = config.get(
            'health_handler_function_name', 'TenULabsHealthHandler'
        )
        role_name = f"{function_name}ServiceRole"
        response = iam_client.get_role(RoleName=role_name)
        assume_role_policy = response['Role']['AssumeRolePolicyDocument']
        statements = assume_role_policy.get('Statement', [])
        lambda_trusted = any(
            stmt.get('Principal', {}).get('Service') == 'lambda.amazonaws.com'
            for stmt in statements
        )
        assert lambda_trusted, (
            f"IAM role '{role_name}' does not trust lambda.amazonaws.com"
        )
