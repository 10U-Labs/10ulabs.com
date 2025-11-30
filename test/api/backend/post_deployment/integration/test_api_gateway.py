from .conftest import get_api_gateway_id_by_name


def test_api_gateway_stage_configuration(apigateway_client, config):
    api_name = config["api_gateway_name"]
    api_id = get_api_gateway_id_by_name(apigateway_client, api_name)
    stages = apigateway_client.get_stages(restApiId=api_id)
    assert len(stages['item']) > 0


def test_api_gateway_deployment_triggers_correctly(apigateway_client, config):
    api_name = config["api_gateway_name"]
    api_id = get_api_gateway_id_by_name(apigateway_client, api_name)
    deployments = apigateway_client.get_deployments(restApiId=api_id)
    assert len(deployments['items']) > 0


def test_api_gateway_usage_plan_quotas(apigateway_client):
    usage_plans = apigateway_client.get_usage_plans()
    assert len(usage_plans['items']) > 0


def test_api_gateway_usage_plan_throttle_settings(apigateway_client):
    usage_plans = apigateway_client.get_usage_plans()
    plan = usage_plans['items'][0]
    assert "throttle" in plan


def test_api_gateway_api_key_is_enabled(apigateway_client):
    api_keys = apigateway_client.get_api_keys()
    assert len(api_keys['items']) > 0


def test_api_gateway_cloudwatch_logging_enabled(apigateway_client, config):
    api_name = config["api_gateway_name"]
    api_id = get_api_gateway_id_by_name(apigateway_client, api_name)
    stages = apigateway_client.get_stages(restApiId=api_id)
    assert len(stages['item']) > 0


def test_api_gateway_request_validation_enabled(apigatewayv2_client):
    apis = apigatewayv2_client.get_apis()
    if apis['Items']:
        api_id = apis['Items'][0]['ApiId']
        routes = apigatewayv2_client.get_routes(ApiId=api_id)
        assert routes['Items']


def test_api_gateway_throttling_settings_configured(apigatewayv2_client):
    apis = apigatewayv2_client.get_apis()
    if apis['Items']:
        api_id = apis['Items'][0]['ApiId']
        stages = apigatewayv2_client.get_stages(ApiId=api_id)
        assert stages['Items']


def test_api_gateway_v2_cloudwatch_logging_enabled(apigatewayv2_client):
    apis = apigatewayv2_client.get_apis()
    if apis['Items']:
        api_id = apis['Items'][0]['ApiId']
        integrations = apigatewayv2_client.get_integrations(ApiId=api_id)
        assert integrations


def test_api_gateway_custom_domain_exists(apigatewayv2_client):
    domain_names = apigatewayv2_client.get_domain_names()
    assert domain_names
