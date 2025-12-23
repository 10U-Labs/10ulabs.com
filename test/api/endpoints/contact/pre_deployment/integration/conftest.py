"""Pytest fixtures for contact endpoint pre-deployment integration tests.

Common fixtures (api_backend_outputs, apigateway_client, ses_client, sts_client,
iam_client, lambda_client, ssm_client) are inherited from test/api/conftest.py.
"""

import pytest
from botocore.exceptions import ClientError


@pytest.fixture(scope="module")
def api_gateway_info(apigateway_client, api_backend_outputs):
    """Get API Gateway info, handling missing/not-found cases gracefully."""
    api_id = api_backend_outputs.get("api_gateway_rest_api_id")
    if not api_id:
        return {"id": None, "exists": False, "accessible": False}

    try:
        response = apigateway_client.get_rest_api(restApiId=api_id)
        endpoint_config = response.get("endpointConfiguration", {})
        resources_response = apigateway_client.get_resources(restApiId=api_id)
        paths = [r.get("path", "") for r in resources_response.get("items", [])]
        return {
            "id": api_id,
            "exists": True,
            "accessible": True,
            "endpoint_types": endpoint_config.get("types", []),
            "paths": paths
        }
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "AccessDeniedException":
            return {"id": api_id, "exists": None, "accessible": False}
        if error_code == "NotFoundException":
            return {"id": api_id, "exists": False, "accessible": True}
        raise
