"""Pytest fixtures for pre-deployment integration tests.

Common fixtures (api_backend_outputs, ecs_runner_outputs, apigateway_client,
sts_client, iam_client, lambda_client, s3_client, dynamodb_client, api_gateway_info)
are inherited from test/api/conftest.py and test_fixtures.aws.
"""

from test_fixtures.integration import create_www_shared_fixtures


pytest_plugins = ['pytest_layers']


# Create www_shared fixtures
www_shared_terraform_initialized, www_shared_outputs = create_www_shared_fixtures()
