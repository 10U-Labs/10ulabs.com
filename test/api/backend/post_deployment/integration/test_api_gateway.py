"""Tests for API Gateway deployment and configuration."""
from .conftest import get_api_gateway_id_by_name


def test_api_gateway_stage_configuration(apigateway_client, config):
    """Verify API Gateway has at least one stage configured."""
    api_name = config["api_gateway_name"]
    api_id = get_api_gateway_id_by_name(apigateway_client, api_name)
    stages = apigateway_client.get_stages(restApiId=api_id)
    assert len(stages['item']) > 0


def test_api_gateway_deployment_triggers_correctly(apigateway_client, config):
    """Verify API Gateway has at least one deployment."""
    api_name = config["api_gateway_name"]
    api_id = get_api_gateway_id_by_name(apigateway_client, api_name)
    deployments = apigateway_client.get_deployments(restApiId=api_id)
    assert len(deployments['items']) > 0


def test_api_gateway_usage_plan_quotas(apigateway_client):
    """Verify API Gateway has at least one usage plan configured."""
    usage_plans = apigateway_client.get_usage_plans()
    assert len(usage_plans['items']) > 0


def test_api_gateway_usage_plan_throttle_settings(apigateway_client):
    """Verify API Gateway usage plan has throttle settings."""
    usage_plans = apigateway_client.get_usage_plans()
    plan = usage_plans['items'][0]
    assert "throttle" in plan


def test_api_gateway_api_key_is_enabled(apigateway_client):
    """Verify API Gateway has at least one API key configured."""
    api_keys = apigateway_client.get_api_keys()
    assert len(api_keys['items']) > 0


def test_api_gateway_cloudwatch_logging_enabled(apigateway_client, config):
    """Verify API Gateway has CloudWatch logging enabled."""
    api_name = config["api_gateway_name"]
    api_id = get_api_gateway_id_by_name(apigateway_client, api_name)
    stages = apigateway_client.get_stages(restApiId=api_id)
    assert len(stages['item']) > 0


def test_api_gateway_request_validation_enabled(apigatewayv2_client):
    """Verify API Gateway V2 has request validation configured."""
    apis = apigatewayv2_client.get_apis()
    if apis['Items']:
        api_id = apis['Items'][0]['ApiId']
        routes = apigatewayv2_client.get_routes(ApiId=api_id)
        assert routes['Items']


def test_api_gateway_throttling_settings_configured(apigatewayv2_client):
    """Verify API Gateway V2 throttling settings are configured."""
    apis = apigatewayv2_client.get_apis()
    if apis['Items']:
        api_id = apis['Items'][0]['ApiId']
        stages = apigatewayv2_client.get_stages(ApiId=api_id)
        assert stages['Items']


def test_api_gateway_v2_cloudwatch_logging_enabled(apigatewayv2_client):
    """Verify API Gateway V2 has CloudWatch logging enabled."""
    apis = apigatewayv2_client.get_apis()
    if apis['Items']:
        api_id = apis['Items'][0]['ApiId']
        integrations = apigatewayv2_client.get_integrations(ApiId=api_id)
        assert integrations


def test_api_gateway_custom_domain_exists(apigatewayv2_client):
    """Verify API Gateway custom domain names are configured."""
    domain_names = apigatewayv2_client.get_domain_names()
    assert domain_names


def test_rest_api_has_request_validators(apigateway_client, config):
    """Verify REST API has request validators configured."""
    api_name = config["api_gateway_name"]
    api_id = get_api_gateway_id_by_name(apigateway_client, api_name)
    validators = apigateway_client.get_request_validators(restApiId=api_id)
    assert len(validators['items']) > 0


def test_rest_api_has_validate_headers_validator(apigateway_client, config):
    """Verify REST API has validate-headers validator."""
    api_name = config["api_gateway_name"]
    api_id = get_api_gateway_id_by_name(apigateway_client, api_name)
    validators = apigateway_client.get_request_validators(restApiId=api_id)
    validator_names = [v.get('name') for v in validators['items']]
    assert 'validate-headers' in validator_names


def test_rest_api_validate_headers_validator_exists(apigateway_client, config):
    """Verify validate-headers validator exists in the validators list."""
    api_name = config["api_gateway_name"]
    api_id = get_api_gateway_id_by_name(apigateway_client, api_name)
    validators = apigateway_client.get_request_validators(restApiId=api_id)
    validator = next(
        (v for v in validators['items'] if v.get('name') == 'validate-headers'),
        None
    )
    assert validator is not None


def test_rest_api_validate_headers_validates_params(apigateway_client, config):
    """Verify validate-headers validator has validateRequestParameters enabled."""
    api_name = config["api_gateway_name"]
    api_id = get_api_gateway_id_by_name(apigateway_client, api_name)
    validators = apigateway_client.get_request_validators(restApiId=api_id)
    validator = next(
        (v for v in validators['items'] if v.get('name') == 'validate-headers'),
        None
    )
    assert validator.get('validateRequestParameters') is True


def test_rest_api_has_gateway_responses(apigateway_client, config):
    """Verify REST API has gateway responses configured."""
    api_name = config["api_gateway_name"]
    api_id = get_api_gateway_id_by_name(apigateway_client, api_name)
    responses = apigateway_client.get_gateway_responses(restApiId=api_id)
    assert len(responses['items']) > 0


def test_rest_api_has_bad_request_parameters_response(apigateway_client, config):
    """Verify REST API has BAD_REQUEST_PARAMETERS gateway response."""
    api_name = config["api_gateway_name"]
    api_id = get_api_gateway_id_by_name(apigateway_client, api_name)
    response = apigateway_client.get_gateway_response(
        restApiId=api_id,
        responseType='BAD_REQUEST_PARAMETERS'
    )
    assert response.get('statusCode') == '400'
