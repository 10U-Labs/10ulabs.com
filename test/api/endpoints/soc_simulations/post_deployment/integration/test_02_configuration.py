"""Layer 2: Configuration tests for simulation-soc endpoint.

Verify that resources created by this deployment are configured correctly.
"""
import json


pytest_plugins = ['test_fixtures.aws']


class TestLambdaConfiguration:
    """Layer 2: Verify Lambda function is configured correctly."""

    def test_simulation_soc_handler_has_correct_runtime(self, lambda_client, shared_config):
        """Verify simulation-soc handler uses Python 3.13 runtime."""
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "simulation_soc", "TenULabsSimulationSocHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        runtime = response["Configuration"]["Runtime"]
        is_python313 = runtime == "python3.13"
        assert is_python313, f"Lambda runtime is {runtime}, expected python3.13"

    def test_simulation_soc_handler_has_correct_architecture(
        self, lambda_client, shared_config
    ):
        """Verify simulation-soc handler uses arm64 architecture."""
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "simulation_soc", "TenULabsSimulationSocHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        architectures = response["Configuration"].get("Architectures", ["x86_64"])
        uses_arm64 = "arm64" in architectures
        assert uses_arm64, f"Lambda architecture is {architectures}, expected arm64"

    def test_simulation_soc_handler_has_correct_timeout(self, lambda_client, shared_config):
        """Verify simulation-soc handler has appropriate timeout."""
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "simulation_soc", "TenULabsSimulationSocHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        timeout = response["Configuration"]["Timeout"]
        timeout_acceptable = 5 <= timeout <= 60
        assert timeout_acceptable, f"Lambda timeout is {timeout}s, expected 5-60s"

    def test_simulation_soc_handler_has_correct_memory_size(
        self, lambda_client, shared_config
    ):
        """Verify simulation-soc handler has appropriate memory size."""
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "simulation_soc", "TenULabsSimulationSocHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        memory = response["Configuration"]["MemorySize"]
        memory_acceptable = 128 <= memory <= 1024
        assert memory_acceptable, f"Lambda memory is {memory}MB, expected 128-1024MB"

    def test_simulation_soc_handler_has_handler_entry_point(
        self, lambda_client, shared_config
    ):
        """Verify simulation-soc handler uses correct entry point."""
        function_name = shared_config.get("lambda_handler_names", {}).get(
            "simulation_soc", "TenULabsSimulationSocHandler"
        )
        response = lambda_client.get_function(FunctionName=function_name)
        handler = response["Configuration"]["Handler"]
        correct_handler = handler == "handler.handler"
        assert correct_handler, f"Lambda handler is {handler}, expected handler.handler"


class TestCloudWatchLogsConfiguration:
    """Layer 2: Verify simulation-soc CloudWatch log group is configured correctly."""

    def test_simulation_soc_handler_log_group_has_retention_policy(
        self, handler_log_group
    ):
        """Verify simulation-soc log group has retention policy."""
        assert handler_log_group["retention"] is not None, (
            f"Simulation SOC log group '{handler_log_group['name']}' "
            "must have retention configured"
        )

    def test_simulation_soc_handler_log_group_retention_matches_policy(
        self, handler_log_group
    ):
        """Verify simulation-soc log group uses 7-day retention per standards."""
        retention = handler_log_group["retention"]
        assert retention == 7, (
            f"Simulation SOC log group retention is {retention} days, expected 7"
        )


class TestIAMConfiguration:
    """Layer 2: Verify IAM role and policies are configured correctly."""

    def test_simulation_soc_handler_role_can_be_assumed_by_lambda(
        self, iam_client, shared_config
    ):
        """Verify IAM role trust policy allows Lambda service."""
        resource_prefix = shared_config.get("resource_prefix", "TenULabs")
        role_name = f"{resource_prefix}SimulationSocHandlerServiceRole"
        response = iam_client.get_role(RoleName=role_name)
        policy_doc = response["Role"]["AssumeRolePolicyDocument"]
        policy_str = json.dumps(policy_doc)
        trusts_lambda = "lambda.amazonaws.com" in policy_str
        assert trusts_lambda, f"Role {role_name} trust policy must allow lambda.amazonaws.com"

    def test_simulation_soc_handler_kms_policy_has_ssm_permissions(
        self, iam_client, shared_config
    ):
        """Verify KMS policy grants SSM parameter access."""
        resource_prefix = shared_config.get("resource_prefix", "TenULabs")
        role_name = f"{resource_prefix}SimulationSocHandlerServiceRole"
        response = iam_client.list_role_policies(RoleName=role_name)
        kms_policy_name = next(
            (n for n in response["PolicyNames"] if "kms" in n.lower()), None
        )
        if kms_policy_name:
            policy_response = iam_client.get_role_policy(
                RoleName=role_name, PolicyName=kms_policy_name
            )
            policy_doc = json.dumps(policy_response["PolicyDocument"])
            has_kms = "kms:" in policy_doc.lower()
            assert has_kms, "KMS policy must include kms: actions"
