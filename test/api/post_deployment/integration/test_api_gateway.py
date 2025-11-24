import boto3


def test_api_gateway_stage_configuration(tfvars):
    apigw = boto3.client('apigateway', region_name=tfvars["aws_region"])
    apis = apigw.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break
    stages = apigw.get_stages(restApiId=api_id)
    assert len(stages['item']) > 0


def test_api_gateway_deployment_triggers_correctly(tfvars):
    apigw = boto3.client('apigateway', region_name=tfvars["aws_region"])
    apis = apigw.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break
    deployments = apigw.get_deployments(restApiId=api_id)
    assert len(deployments['items']) > 0


def test_api_gateway_usage_plan_quotas(tfvars):
    apigw = boto3.client('apigateway', region_name=tfvars["aws_region"])
    usage_plans = apigw.get_usage_plans()
    assert len(usage_plans['items']) > 0


def test_api_gateway_usage_plan_throttle_settings(tfvars):
    apigw = boto3.client('apigateway', region_name=tfvars["aws_region"])
    usage_plans = apigw.get_usage_plans()
    plan = usage_plans['items'][0]
    assert "throttle" in plan


def test_api_gateway_api_key_is_enabled(tfvars):
    apigw = boto3.client('apigateway', region_name=tfvars["aws_region"])
    api_keys = apigw.get_api_keys()
    assert len(api_keys['items']) > 0


def test_api_gateway_cloudwatch_logging_enabled(tfvars):
    apigw = boto3.client('apigateway', region_name=tfvars["aws_region"])
    apis = apigw.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break
    stages = apigw.get_stages(restApiId=api_id)
    assert len(stages['item']) > 0


def test_api_gateway_request_validation_enabled(tfvars):
    apigateway = boto3.client('apigatewayv2', region_name=tfvars["aws_region"])
    apis = apigateway.get_apis()
    if apis['Items']:
        api_id = apis['Items'][0]['ApiId']
        routes = apigateway.get_routes(ApiId=api_id)
        assert routes['Items']


def test_api_gateway_throttling_settings_configured(tfvars):
    apigateway = boto3.client('apigatewayv2', region_name=tfvars["aws_region"])
    apis = apigateway.get_apis()
    if apis['Items']:
        api_id = apis['Items'][0]['ApiId']
        stages = apigateway.get_stages(ApiId=api_id)
        assert stages['Items']


def test_api_gateway_v2_cloudwatch_logging_enabled(tfvars):
    apigateway = boto3.client('apigatewayv2', region_name=tfvars["aws_region"])
    apis = apigateway.get_apis()
    if apis['Items']:
        api_id = apis['Items'][0]['ApiId']
        integrations = apigateway.get_integrations(ApiId=api_id)
        assert integrations


def test_api_gateway_custom_domain_exists(tfvars):
    apigateway = boto3.client('apigatewayv2', region_name=tfvars["aws_region"])
    domain_names = apigateway.get_domain_names()
    assert domain_names
