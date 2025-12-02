def test_health_handler_subscription_filter_exists(logs_client, config):
    response = logs_client.describe_subscription_filters(logGroupName=config['health_handler_log_group_name'])
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    has_filter = 'health-handler-to-firehose' in filter_names
    assert has_filter


def test_health_handler_subscription_destinations_firehose(logs_client, config):
    response = logs_client.describe_subscription_filters(logGroupName=config['health_handler_log_group_name'])
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    is_firehose = 'firehose' in destination_arn
    assert is_firehose


def test_catchall_handler_subscription_filter_exists(logs_client, config):
    response = logs_client.describe_subscription_filters(logGroupName=config['catchall_handler_log_group_name'])
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    has_filter = 'catchall-handler-to-firehose' in filter_names
    assert has_filter


def test_catchall_handler_subscription_destinations_firehose(logs_client, config):
    response = logs_client.describe_subscription_filters(logGroupName=config['catchall_handler_log_group_name'])
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    is_firehose = 'firehose' in destination_arn
    assert is_firehose


def test_api_gateway_subscription_filter_exists(logs_client, config):
    response = logs_client.describe_subscription_filters(logGroupName=config['api_gateway_log_group_name'])
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    has_filter = 'api-gateway-to-firehose' in filter_names
    assert has_filter


def test_api_gateway_subscription_destinations_firehose(logs_client, config):
    response = logs_client.describe_subscription_filters(logGroupName=config['api_gateway_log_group_name'])
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    is_firehose = 'firehose' in destination_arn
    assert is_firehose


def test_waf_subscription_filter_exists():
    logs_client_east = __import__('boto3').client('logs', region_name='us-east-1')
    log_group_name = 'aws-waf-logs-api'
    response = logs_client_east.describe_subscription_filters(logGroupName=log_group_name)
    filter_names = [f['filterName'] for f in response['subscriptionFilters']]
    has_filter = 'waf-to-firehose' in filter_names
    assert has_filter


def test_waf_subscription_destinations_firehose():
    logs_client_east = __import__('boto3').client('logs', region_name='us-east-1')
    log_group_name = 'aws-waf-logs-api'
    response = logs_client_east.describe_subscription_filters(logGroupName=log_group_name)
    destination_arn = response['subscriptionFilters'][0]['destinationArn']
    is_firehose = 'firehose' in destination_arn
    assert is_firehose
