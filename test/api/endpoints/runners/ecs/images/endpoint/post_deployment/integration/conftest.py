"""Fixtures for runners/ecs/images endpoint post-deployment integration tests."""
from test.api.endpoints.runners.ecs.images.endpoint.helpers import (
    ApiRequestConfig,
    ApiRequestParams,
    make_api_request,
)

import pytest

from test_fixtures.aws import get_log_group_info

@pytest.fixture(scope="session")
def api_request(request):
    """Provide a function to make API requests."""
    fqdn = request.getfixturevalue('api_fqdn')
    key = request.getfixturevalue('api_key')
    config = ApiRequestConfig(fqdn=fqdn, api_key=key, test_mode_default=True)

    def _make_request(path, method="GET", headers=None, body=None):
        params = ApiRequestParams(path=path, method=method, headers=headers, body=body)
        return make_api_request(config, params)

    return _make_request


@pytest.fixture(name="lambda_function", scope="module")
def lambda_function_fixture(lambda_client):
    """Find and return the Lambda function matching ImageForEcsRunners."""
    response = lambda_client.list_functions()
    matching = [
        f for f in response["Functions"]
        if "ImageForEcsRunners" in f["FunctionName"]
    ]
    if not matching:
        pytest.fail(
            "No Lambda function found matching 'ImageForEcsRunners'. "
            "Run terraform apply in src/api/endpoints/runners/ecs/images/"
        )
    return matching[0]


@pytest.fixture(name="lambda_config", scope="module")
def lambda_config_fixture(lambda_client, lambda_function):
    """Get the Lambda function configuration."""
    return lambda_client.get_function_configuration(
        FunctionName=lambda_function["FunctionName"]
    )


@pytest.fixture(name="env_vars", scope="module")
def env_vars_fixture(lambda_config):
    """Get environment variables from Lambda config."""
    return lambda_config.get("Environment", {}).get("Variables", {})


@pytest.fixture(name="handler_log_group", scope="module")
def handler_log_group_fixture(logs_client, lambda_function):
    """Get the Lambda handler log group info from CloudWatch."""
    function_name = lambda_function["FunctionName"]
    log_group_name = f"/aws/lambda/{function_name}"
    return get_log_group_info(logs_client, log_group_name)


@pytest.fixture(name="lambda_role_name", scope="module")
def lambda_role_name_fixture(lambda_function):
    """Extract the IAM role name from the Lambda function's Role ARN."""
    role_arn = lambda_function["Role"]
    return role_arn.split("/")[-1]


@pytest.fixture(name="lambda_role", scope="module")
def lambda_role_fixture(iam_client, lambda_role_name):
    """Get the Lambda IAM role details."""
    response = iam_client.get_role(RoleName=lambda_role_name)
    return response["Role"]


@pytest.fixture(name="lambda_role_policies", scope="module")
def lambda_role_policies_fixture(iam_client, lambda_role_name):
    """Get all policies attached to the Lambda role."""
    attached = iam_client.list_attached_role_policies(RoleName=lambda_role_name)
    inline = iam_client.list_role_policies(RoleName=lambda_role_name)
    return {
        "attached": attached.get("AttachedPolicies", []),
        "inline": inline.get("PolicyNames", [])
    }
