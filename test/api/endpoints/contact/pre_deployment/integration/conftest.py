"""Pytest fixtures for contact endpoint pre-deployment integration tests.

Common fixtures (api_backend_outputs, apigateway_client, ses_client, sts_client,
iam_client, lambda_client, ssm_client, api_gateway_info) are inherited from
test/api/conftest.py and test_fixtures.aws.
"""

pytest_plugins = ['pytest_layers']

# All fixtures inherited from parent conftest and test_fixtures.aws
