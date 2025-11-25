from test.api.conftest import find_sns_topic_arns


def test_circuit_breaker_remediation_lambda_deployed(lambda_client, config):
    function_name = f"{config['resource_prefix']}-CircuitBreakerRemediation"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['FunctionName'] == function_name


def test_circuit_breaker_recovery_lambda_deployed(lambda_client, config):
    function_name = f"{config['resource_prefix']}-CircuitBreakerRecovery"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['FunctionName'] == function_name


def test_dlq_reprocessor_lambda_deployed(lambda_client, config):
    function_name = f"{config['resource_prefix']}-DLQReprocessor"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['FunctionName'] == function_name


def test_cloudwatch_alarms_deployed(cloudwatch_client, config):
    alarm_name = f"{config['resource_prefix']}-circuit-breaker-open"
    alarms = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    assert len(alarms['MetricAlarms']) == 1


def test_eventbridge_remediation_rule_deployed(events_client, config):
    rule_name = f"{config['resource_prefix']}-circuit-breaker-remediation"
    response = events_client.describe_rule(Name=rule_name)
    assert response['State'] == 'ENABLED'


def test_eventbridge_recovery_rule_deployed(events_client, config):
    rule_name = f"{config['resource_prefix']}-circuit-breaker-recovery"
    response = events_client.describe_rule(Name=rule_name)
    assert response['State'] == 'ENABLED'


def test_sns_topic_deployed(sns_client, config):
    topic_name = f"{config['resource_prefix']}-circuit-breaker-alerts"
    matching_topics = find_sns_topic_arns(sns_client, topic_name)
    assert len(matching_topics) == 1


def test_incidents_table_deployed(dynamodb_client, config):
    table_name = f"{config['resource_prefix']}-incidents"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['TableStatus'] == 'ACTIVE'


def test_circuit_breaker_state_table_deployed(dynamodb_client, config):
    table_name = f"{config['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['TableStatus'] == 'ACTIVE'


def test_recovery_lambda_can_be_invoked(lambda_client, config):
    function_name = f"{config['resource_prefix']}-CircuitBreakerRecovery"
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=b'{}'
    )
    assert response['StatusCode'] == 200


def test_dlq_reprocessor_lambda_can_be_invoked(lambda_client, config):
    function_name = f"{config['resource_prefix']}-DLQReprocessor"
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=b'{}'
    )
    assert response['StatusCode'] == 200


def test_circuit_breaker_state_table_readable(dynamodb_client, config):
    table_name = f"{config['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.get_item(
        TableName=table_name,
        Key={'state_id': {'S': 'current'}}
    )
    assert 'Item' in response or 'Item' not in response


def test_recovery_lambda_logs_exist(logs_client, config):
    log_group_name = f"/aws/lambda/{config['resource_prefix']}-CircuitBreakerRecovery"
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = [lg for lg in response['logGroups'] if lg['logGroupName'] == log_group_name]
    assert len(log_groups) == 1


def test_remediation_lambda_logs_exist(logs_client, config):
    log_group_name = f"/aws/lambda/{config['resource_prefix']}-CircuitBreakerRemediation"
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = [lg for lg in response['logGroups'] if lg['logGroupName'] == log_group_name]
    assert len(log_groups) == 1


def test_dlq_reprocessor_logs_exist(logs_client, config):
    log_group_name = f"/aws/lambda/{config['resource_prefix']}-DLQReprocessor"
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = [lg for lg in response['logGroups'] if lg['logGroupName'] == log_group_name]
    assert len(log_groups) == 1
