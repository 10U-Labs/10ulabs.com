def test_health_handler_subscription_filter_exists(logs_client):
    log_group_name = '/aws/lambda/TenULabsHealthHandler'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'health-handler-to-firehose' in filter_names


def test_health_handler_subscription_destinations_firehose(logs_client):
    log_group_name = '/aws/lambda/TenULabsHealthHandler'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'firehose' in destination_arn


def test_catchall_handler_subscription_filter_exists(logs_client):
    log_group_name = '/aws/lambda/TenULabsCatchAllHandler'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'catchall-handler-to-firehose' in filter_names


def test_catchall_handler_subscription_destinations_firehose(logs_client):
    log_group_name = '/aws/lambda/TenULabsCatchAllHandler'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'firehose' in destination_arn


def test_runners_handler_subscription_filter_exists(logs_client):
    log_group_name = '/aws/lambda/TenULabsWebhookHandler'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'runners-handler-to-firehose' in filter_names


def test_runners_handler_subscription_destinations_firehose(logs_client):
    log_group_name = '/aws/lambda/TenULabsWebhookHandler'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'firehose' in destination_arn


def test_v1_handler_subscription_filter_exists(logs_client):
    log_group_name = '/aws/lambda/TenULabsV1ApiHandler'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'v1-handler-to-firehose' in filter_names


def test_v1_handler_subscription_destinations_firehose(logs_client):
    log_group_name = '/aws/lambda/TenULabsV1ApiHandler'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'firehose' in destination_arn


def test_circuit_breaker_remediation_subscription_filter_exists(logs_client):
    log_group_name = '/aws/lambda/TenULabs-CircuitBreakerRemediation'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'circuit-breaker-remediation-to-firehose' in filter_names


def test_circuit_breaker_remediation_subscription_destinations_firehose(logs_client):
    log_group_name = '/aws/lambda/TenULabs-CircuitBreakerRemediation'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'firehose' in destination_arn


def test_dlq_reprocessor_subscription_filter_exists(logs_client):
    log_group_name = '/aws/lambda/TenULabs-DLQReprocessor'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'dlq-reprocessor-to-firehose' in filter_names


def test_dlq_reprocessor_subscription_destinations_firehose(logs_client):
    log_group_name = '/aws/lambda/TenULabs-DLQReprocessor'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'firehose' in destination_arn


def test_circuit_breaker_recovery_subscription_filter_exists(logs_client):
    log_group_name = '/aws/lambda/TenULabs-CircuitBreakerRecovery'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'circuit-breaker-recovery-to-firehose' in filter_names


def test_circuit_breaker_recovery_subscription_destinations_firehose(logs_client):
    log_group_name = '/aws/lambda/TenULabs-CircuitBreakerRecovery'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'firehose' in destination_arn


def test_api_gateway_subscription_filter_exists(logs_client):
    log_group_name = '/aws/apigateway/TenULabsApi'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'api-gateway-to-firehose' in filter_names


def test_api_gateway_subscription_destinations_firehose(logs_client):
    log_group_name = '/aws/apigateway/TenULabsApi'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'firehose' in destination_arn


def test_ecs_runner_subscription_filter_exists(logs_client):
    log_group_name = '/ecs/github-runner'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'ecs-runner-to-firehose' in filter_names


def test_ecs_runner_subscription_destinations_firehose(logs_client):
    log_group_name = '/ecs/github-runner'
    response = logs_client.describe_subscription_filters(logGroupName=log_group_name)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'firehose' in destination_arn


def test_waf_subscription_filter_exists():
    logs_client_east = __import__('boto3').client('logs', region_name='us-east-1')
    log_group_name = 'aws-waf-logs-api'
    response = logs_client_east.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    assert 'waf-to-firehose' in filter_names


def test_waf_subscription_destinations_firehose():
    logs_client_east = __import__('boto3').client('logs', region_name='us-east-1')
    log_group_name = 'aws-waf-logs-api'
    response = logs_client_east.describe_subscription_filters(logGroupName=log_group_name)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    assert 'firehose' in destination_arn
