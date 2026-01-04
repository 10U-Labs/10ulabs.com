"""Layer 3: Wiring tests.

Verify components are connected properly.
"""
from test.api.endpoints.conftest import assert_lambda_package_includes_file

import pytest
from botocore.exceptions import ClientError



class TestLambdaPackage:
    """Verify Lambda package includes required modules."""

    def test_lambda_package_includes_handler(self, lambda_client, lambda_function_name):
        """Verify deployed Lambda package includes handler.py."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        region = response['Configuration']['FunctionArn'].split(':')[3]
        assert_lambda_package_includes_file(lambda_function_name, "handler.py", region)
        assert True  # Explicit pass

    def test_lambda_package_includes_runner_labels(
        self, lambda_client, lambda_function_name
    ):
        """Verify deployed Lambda package includes runner_labels.py.

        This is a regression test that validates the deployed Lambda package
        actually contains the runner_labels module. The Lambda will fail at
        runtime with a ModuleNotFoundError if this file is missing.
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        region = response['Configuration']['FunctionArn'].split(':')[3]
        assert_lambda_package_includes_file(
            lambda_function_name, "runner_labels.py", region
        )
        assert True  # Explicit pass

    def test_lambda_package_includes_runners_json(
        self, lambda_client, lambda_function_name
    ):
        """Verify deployed Lambda package includes etc/runners.json.

        This is required by the runner_labels module to determine runner types.
        """
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")
        response = lambda_client.get_function(FunctionName=lambda_function_name)
        region = response['Configuration']['FunctionArn'].split(':')[3]
        assert_lambda_package_includes_file(
            lambda_function_name, "etc/runners.json", region
        )
        assert True  # Explicit pass


class TestLambdaSQSTrigger:
    """Verify Lambda is triggered by SQS queue."""

    def test_lambda_has_sqs_trigger(self, lambda_client, lambda_function_name, sqs_queue_arn):
        """Verify Lambda has SQS event source mapping."""
        if not lambda_function_name or not sqs_queue_arn:
            pytest.skip("lambda_function_name or sqs_queue_arn not available")
        try:
            response = lambda_client.list_event_source_mappings(
                FunctionName=lambda_function_name,
                EventSourceArn=sqs_queue_arn
            )
            mappings = response.get("EventSourceMappings", [])
            assert len(mappings) > 0, (
                f"Lambda '{lambda_function_name}' has no SQS trigger for queue "
                f"'{sqs_queue_arn}'. Check lambda.tf aws_lambda_event_source_mapping."
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Lambda function does not exist")
            raise

    def test_sqs_trigger_batch_size_is_1(self, sqs_event_source_mapping):
        """Verify SQS trigger batch size is 1."""
        if sqs_event_source_mapping is None:
            pytest.skip("No SQS event source mapping found")
        batch_size = sqs_event_source_mapping.get("BatchSize", 0)
        assert batch_size == 1, (
            f"SQS trigger batch size is {batch_size}, expected 1. "
            "Each runner request should be processed individually."
        )

    def test_sqs_trigger_is_enabled(self, sqs_event_source_mapping):
        """Verify SQS trigger is enabled."""
        if sqs_event_source_mapping is None:
            pytest.skip("No SQS event source mapping found")
        state = sqs_event_source_mapping.get("State", "")
        assert state == "Enabled", (
            f"SQS trigger state is '{state}', expected 'Enabled'. "
            "The Lambda will not process messages if the trigger is disabled."
        )


class TestSQSDLQWiring:
    """Verify SQS queue is wired to DLQ."""

    def test_sqs_redrive_targets_dlq(self, sqs_redrive_policy, sqs_dlq_arn):
        """Verify SQS redrive policy targets the correct DLQ."""
        if sqs_redrive_policy is None:
            pytest.skip("No redrive policy configured")
        if not sqs_dlq_arn:
            pytest.skip("sqs_dlq_arn not available")
        target_arn = sqs_redrive_policy.get("deadLetterTargetArn", "")
        assert target_arn == sqs_dlq_arn, (
            f"SQS redrive targets '{target_arn}', expected '{sqs_dlq_arn}'"
        )

    def test_sqs_max_receive_count_is_3(self, sqs_redrive_policy):
        """Verify SQS max receive count is 3 before sending to DLQ."""
        if sqs_redrive_policy is None:
            pytest.skip("No redrive policy configured")
        max_receive = sqs_redrive_policy.get("maxReceiveCount", 0)
        assert max_receive == 3, (
            f"SQS maxReceiveCount is {max_receive}, expected 3. "
            "Messages should be retried 3 times before going to DLQ."
        )


class TestLambdaEnvironmentVariables:
    """Verify Lambda environment variables are set correctly."""

    def test_lambda_has_api_base_url_var(self, lambda_client, lambda_function_name):
        """Verify Lambda has API_BASE_URL environment variable."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")
        try:
            response = lambda_client.get_function_configuration(
                FunctionName=lambda_function_name
            )
            env_vars = response.get("Environment", {}).get("Variables", {})
            assert "API_BASE_URL" in env_vars, (
                f"Lambda '{lambda_function_name}' missing API_BASE_URL environment variable"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Lambda function does not exist")
            raise

    def test_lambda_api_base_url_uses_https(self, lambda_client, lambda_function_name):
        """Verify Lambda API_BASE_URL uses HTTPS."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")
        try:
            response = lambda_client.get_function_configuration(
                FunctionName=lambda_function_name
            )
            env_vars = response.get("Environment", {}).get("Variables", {})
            if "API_BASE_URL" not in env_vars:
                pytest.skip("API_BASE_URL not set")
            assert env_vars["API_BASE_URL"].startswith("https://"), (
                f"API_BASE_URL should start with https://, got: {env_vars['API_BASE_URL']}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Lambda function does not exist")
            raise

    def test_lambda_has_api_key_parameter_name_var(self, lambda_client, lambda_function_name):
        """Verify Lambda has API_KEY_PARAMETER_NAME environment variable."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")
        try:
            response = lambda_client.get_function_configuration(
                FunctionName=lambda_function_name
            )
            env_vars = response.get("Environment", {}).get("Variables", {})
            assert "API_KEY_PARAMETER_NAME" in env_vars, (
                f"Lambda '{lambda_function_name}' missing API_KEY_PARAMETER_NAME "
                "environment variable"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Lambda function does not exist")
            raise

    def test_lambda_api_key_parameter_name_is_ssm_path(
        self, lambda_client, lambda_function_name
    ):
        """Verify Lambda API_KEY_PARAMETER_NAME is an SSM parameter path."""
        if not lambda_function_name:
            pytest.skip("lambda_function_name not available")
        try:
            response = lambda_client.get_function_configuration(
                FunctionName=lambda_function_name
            )
            env_vars = response.get("Environment", {}).get("Variables", {})
            if "API_KEY_PARAMETER_NAME" not in env_vars:
                pytest.skip("API_KEY_PARAMETER_NAME not set")
            assert env_vars["API_KEY_PARAMETER_NAME"].startswith("/"), (
                "API_KEY_PARAMETER_NAME should be an SSM parameter path starting with /, "
                f"got: {env_vars['API_KEY_PARAMETER_NAME']}"
            )
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                pytest.skip("Lambda function does not exist")
            raise
