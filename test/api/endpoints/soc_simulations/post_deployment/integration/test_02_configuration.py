"""Layer 2: Configuration tests for simulation-soc endpoint.

Verify that resources created by this deployment are configured correctly.
"""


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
