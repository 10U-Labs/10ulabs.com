import json
import boto3


def test_stack_deployed_successfully(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi-Runners')
    assert len(stacks['Stacks']) == 1


def test_stack_status_is_complete(cloudformation_client):
    stacks = cloudformation_client.describe_stacks(StackName='TenULabsApi-Runners')
    stack_status = stacks['Stacks'][0]['StackStatus']
    assert stack_status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']


def test_webhook_router_lambda_exists(lambda_client, function_name):
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['FunctionName'] == function_name


def test_webhook_router_lambda_has_correct_runtime(lambda_client, function_name):
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['Runtime'] == 'python3.14'


def test_webhook_router_lambda_has_correct_timeout(lambda_client, function_name, config):
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['Timeout'] == config['aws']['lambda']['timeout_seconds']


def test_webhook_router_lambda_has_correct_memory(lambda_client, function_name, config):
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['MemorySize'] == config['aws']['lambda']['memory_mb']


def test_webhook_router_lambda_has_webhook_secret_env_var(lambda_client, function_name):
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response['Configuration']['Environment']['Variables']
    assert 'WEBHOOK_SECRET_NAME' in env_vars


def test_webhook_router_lambda_has_api_base_url_env_var(lambda_client, function_name):
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response['Configuration']['Environment']['Variables']
    assert 'API_BASE_URL' in env_vars


def test_webhook_router_lambda_has_execution_role(lambda_client, function_name):
    response = lambda_client.get_function(FunctionName=function_name)
    assert 'Role' in response['Configuration']


def test_webhook_router_lambda_has_secrets_manager_permission(lambda_client, function_name, config):
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


def test_api_gateway_runners_resource_exists(apigw_client):
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

    assert 'POST' in runners_resource['resourceMethods']


def test_webhook_router_lambda_can_be_invoked(lambda_client, function_name):
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


def test_webhook_router_lambda_returns_200_for_ping(lambda_client, function_name):
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


def test_webhook_router_lambda_returns_pong_message(lambda_client, function_name):
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
    body = json.loads(payload['body'])
    assert body['message'] == 'pong'


def test_webhook_router_lambda_has_cloudwatch_log_group(lambda_client, function_name, config):
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


def test_api_gateway_can_invoke_webhook_router_lambda(lambda_client, function_name):
    policy = lambda_client.get_policy(FunctionName=function_name)
    assert 'apigateway.amazonaws.com' in policy['Policy']


def test_webhook_config_lambda_exists(lambda_client, function_name):
    config_function_name = f"{function_name}-config"
    response = lambda_client.get_function(FunctionName=config_function_name)
    assert response['Configuration']['FunctionName'] == config_function_name


def test_webhook_config_lambda_has_correct_runtime(lambda_client, function_name):
    config_function_name = f"{function_name}-config"
    response = lambda_client.get_function(FunctionName=config_function_name)
    assert response['Configuration']['Runtime'] == 'python3.14'


def test_webhook_config_lambda_has_correct_timeout(lambda_client, function_name):
    config_function_name = f"{function_name}-config"
    response = lambda_client.get_function(FunctionName=config_function_name)
    assert response['Configuration']['Timeout'] == 60


def test_webhook_config_lambda_has_correct_memory(lambda_client, function_name):
    config_function_name = f"{function_name}-config"
    response = lambda_client.get_function(FunctionName=config_function_name)
    assert response['Configuration']['MemorySize'] == 256


def test_webhook_config_lambda_has_webhook_secret_env_var(lambda_client, function_name):
    config_function_name = f"{function_name}-config"
    response = lambda_client.get_function(FunctionName=config_function_name)
    env_vars = response['Configuration']['Environment']['Variables']
    assert 'WEBHOOK_SECRET_NAME' in env_vars


def test_webhook_config_lambda_has_github_pat_secret_env_var(lambda_client, function_name):
    config_function_name = f"{function_name}-config"
    response = lambda_client.get_function(FunctionName=config_function_name)
    env_vars = response['Configuration']['Environment']['Variables']
    assert 'GITHUB_PAT_SECRET_NAME' in env_vars


def test_webhook_config_lambda_has_execution_role(lambda_client, function_name):
    config_function_name = f"{function_name}-config"
    response = lambda_client.get_function(FunctionName=config_function_name)
    assert 'Role' in response['Configuration']


def test_webhook_config_lambda_has_secrets_manager_permission(lambda_client, function_name, config):
    iam_client = boto3.client('iam', region_name=config['aws']['region'])

    config_function_name = f"{function_name}-config"
    response = lambda_client.get_function(FunctionName=config_function_name)
    role_arn = response['Configuration']['Role']
    role_name = role_arn.split('/')[-1]

    inline_policies = iam_client.list_role_policies(RoleName=role_name)

    has_get_secret_permission = False
    has_create_secret_permission = False

    for policy_name in inline_policies['PolicyNames']:
        policy_doc = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        policy_str = json.dumps(policy_doc['PolicyDocument'])
        if 'secretsmanager:GetSecretValue' in policy_str:
            has_get_secret_permission = True
        if 'secretsmanager:CreateSecret' in policy_str:
            has_create_secret_permission = True

    assert has_get_secret_permission and has_create_secret_permission


def test_webhook_config_lambda_has_cloudwatch_log_group(lambda_client, function_name, config):
    logs_client = boto3.client('logs', region_name=config['aws']['region'])
    config_function_name = f"{function_name}-config"
    log_groups = logs_client.describe_log_groups(logGroupNamePrefix=f'/aws/lambda/{config_function_name}')
    assert len(log_groups['logGroups']) > 0


def test_webhook_router_lambda_has_idempotency_table_env_var(lambda_client, function_name):
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response['Configuration']['Environment']['Variables']
    assert 'IDEMPOTENCY_TABLE_NAME' in env_vars


def test_webhook_router_lambda_has_dead_letter_queue_configured(lambda_client, function_name):
    response = lambda_client.get_function(FunctionName=function_name)
    assert 'DeadLetterConfig' in response['Configuration']


def test_webhook_router_lambda_has_reserved_concurrent_executions(lambda_client, function_name):
    response = lambda_client.get_function(FunctionName=function_name)
    assert 'ReservedConcurrentExecutions' in response['Configuration']


def test_webhook_router_lambda_reserved_concurrent_executions_is_10(lambda_client, function_name):
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['ReservedConcurrentExecutions'] == 10


def test_idempotency_table_exists(function_name, config):
    dynamodb_client = boto3.client('dynamodb', region_name=config['aws']['region'])
    table_name = f"{function_name}-idempotency"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['TableName'] == table_name


def test_idempotency_table_has_ttl_enabled(function_name, config):
    dynamodb_client = boto3.client('dynamodb', region_name=config['aws']['region'])
    table_name = f"{function_name}-idempotency"
    response = dynamodb_client.describe_time_to_live(TableName=table_name)
    assert response['TimeToLiveDescription']['TimeToLiveStatus'] == 'ENABLED'


def test_idempotency_table_has_point_in_time_recovery(function_name, config):
    dynamodb_client = boto3.client('dynamodb', region_name=config['aws']['region'])
    table_name = f"{function_name}-idempotency"
    response = dynamodb_client.describe_continuous_backups(TableName=table_name)
    assert response['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']['PointInTimeRecoveryStatus'] == 'ENABLED'


def test_dead_letter_queue_exists(function_name, config):
    sqs_client = boto3.client('sqs', region_name=config['aws']['region'])
    queue_name = f"{function_name}-dlq"
    response = sqs_client.get_queue_url(QueueName=queue_name)
    assert queue_name in response['QueueUrl']


def test_dead_letter_queue_has_correct_retention_period(function_name, config):
    sqs_client = boto3.client('sqs', region_name=config['aws']['region'])
    queue_name = f"{function_name}-dlq"
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=['MessageRetentionPeriod']
    )
    assert int(attributes['Attributes']['MessageRetentionPeriod']) == 1209600


def test_cloudwatch_alarm_for_errors_exists(function_name, config):
    cloudwatch_client = boto3.client('cloudwatch', region_name=config['aws']['region'])
    alarm_name = f"{function_name}-errors"
    response = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    assert len(response['MetricAlarms']) == 1


def test_cloudwatch_alarm_for_throttles_exists(function_name, config):
    cloudwatch_client = boto3.client('cloudwatch', region_name=config['aws']['region'])
    alarm_name = f"{function_name}-throttles"
    response = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    assert len(response['MetricAlarms']) == 1


def test_cloudwatch_alarm_for_dlq_messages_exists(function_name, config):
    cloudwatch_client = boto3.client('cloudwatch', region_name=config['aws']['region'])
    alarm_name = f"{function_name}-dlq-messages"
    response = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    assert len(response['MetricAlarms']) == 1
