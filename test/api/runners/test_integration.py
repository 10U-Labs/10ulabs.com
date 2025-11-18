import json
import boto3


def test_stack_deployed_successfully(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi-Runners')
    assert len(stacks['Stacks']) == 1


def test_stack_status_is_complete(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi-Runners')
    stack_status = stacks['Stacks'][0]['StackStatus']
    assert stack_status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']


def test_webhook_router_lambda_exists(lambda_client, config):
    function_name = config['aws']['lambda']['function_name']
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['FunctionName'] == function_name


def test_webhook_router_lambda_has_correct_runtime(lambda_client, config):
    function_name = config['aws']['lambda']['function_name']
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['Runtime'] == 'python3.14'


def test_webhook_router_lambda_has_correct_timeout(lambda_client, config):
    function_name = config['aws']['lambda']['function_name']
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['Timeout'] == config['aws']['lambda']['timeout_seconds']


def test_webhook_router_lambda_has_correct_memory(lambda_client, config):
    function_name = config['aws']['lambda']['function_name']
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['MemorySize'] == config['aws']['lambda']['memory_mb']


def test_webhook_router_lambda_has_webhook_secret_env_var(lambda_client, config):
    function_name = config['aws']['lambda']['function_name']
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response['Configuration']['Environment']['Variables']
    assert 'WEBHOOK_SECRET_NAME' in env_vars


def test_webhook_router_lambda_has_api_base_url_env_var(lambda_client, config):
    function_name = config['aws']['lambda']['function_name']
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response['Configuration']['Environment']['Variables']
    assert 'API_BASE_URL' in env_vars


def test_webhook_router_lambda_has_execution_role(lambda_client, config):
    function_name = config['aws']['lambda']['function_name']
    response = lambda_client.get_function(FunctionName=function_name)
    assert 'Role' in response['Configuration']


def test_webhook_router_lambda_has_secrets_manager_permission(lambda_client, config):
    function_name = config['aws']['lambda']['function_name']
    iam_client = boto3.client('iam', region_name=config['aws']['region'])

    response = lambda_client.get_function(FunctionName=function_name)
    role_arn = response['Configuration']['Role']
    role_name = role_arn.split('/')[-1]

    attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)
    inline_policies = iam_client.list_role_policies(RoleName=role_name)

    has_secrets_permission = False

    for policy_name in inline_policies['PolicyNames']:
        policy_doc = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        policy_str = json.dumps(policy_doc['PolicyDocument'])
        if 'secretsmanager:GetSecretValue' in policy_str:
            has_secrets_permission = True
            break

    assert has_secrets_permission


def test_api_gateway_has_runners_resource(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break

    assert api_id is not None

    resources = apigw_client.get_resources(restApiId=api_id)
    resource_paths = [r['path'] for r in resources['items']]
    assert '/v1/runners' in resource_paths


def test_api_gateway_runners_has_post_method(apigw_client):
    apis = apigw_client.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break

    resources = apigw_client.get_resources(restApiId=api_id)
    runners_resource = None
    for r in resources['items']:
        if r['path'] == '/v1/runners':
            runners_resource = r
            break

    assert runners_resource is not None
    assert 'POST' in runners_resource['resourceMethods']


def test_webhook_router_lambda_can_be_invoked(lambda_client, config):
    function_name = config['aws']['lambda']['function_name']
    test_event = {
        'headers': {
            'x-github-event': 'ping'
        },
        'body': json.dumps({
            'zen': 'test'
        })
    }

    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(test_event)
    )

    assert response['StatusCode'] == 200


def test_webhook_router_lambda_returns_valid_response_for_ping(lambda_client, config):
    function_name = config['aws']['lambda']['function_name']
    test_event = {
        'headers': {
            'x-github-event': 'ping'
        },
        'body': json.dumps({
            'zen': 'test'
        })
    }

    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=json.dumps(test_event)
    )

    payload = json.loads(response['Payload'].read())
    assert payload['statusCode'] == 200
    body = json.loads(payload['body'])
    assert body['message'] == 'pong'


def test_webhook_router_lambda_has_cloudwatch_log_group(lambda_client, config):
    function_name = config['aws']['lambda']['function_name']
    logs_client = boto3.client('logs', region_name=config['aws']['region'])
    log_groups = logs_client.describe_log_groups(logGroupNamePrefix=f'/aws/lambda/{function_name}')
    assert len(log_groups['logGroups']) > 0


def test_stack_has_webhook_endpoint_output(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi-Runners')
    outputs = stacks['Stacks'][0].get('Outputs', [])
    output_keys = [o['OutputKey'] for o in outputs]
    assert 'RunnersWebhookEndpoint' in output_keys


def test_stack_has_lambda_name_output(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi-Runners')
    outputs = stacks['Stacks'][0].get('Outputs', [])
    output_keys = [o['OutputKey'] for o in outputs]
    assert 'WebhookRouterLambdaName' in output_keys


def test_api_gateway_can_invoke_webhook_router_lambda(lambda_client, config):
    function_name = config['aws']['lambda']['function_name']
    policy = lambda_client.get_policy(FunctionName=function_name)
    assert 'apigateway.amazonaws.com' in policy['Policy']
