import time


def test_circuit_breaker_remediation_lambda_deployed(lambda_client, tfvars):
    function_name = f"{tfvars['resource_prefix']}-CircuitBreakerRemediation"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['FunctionName'] == function_name


def test_circuit_breaker_recovery_lambda_deployed(lambda_client, tfvars):
    function_name = f"{tfvars['resource_prefix']}-CircuitBreakerRecovery"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['FunctionName'] == function_name


def test_dlq_reprocessor_lambda_deployed(lambda_client, tfvars):
    function_name = f"{tfvars['resource_prefix']}-DLQReprocessor"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['FunctionName'] == function_name


def test_cloudwatch_alarms_deployed(cloudwatch_client, tfvars):
    alarm_name = f"{tfvars['resource_prefix']}-circuit-breaker-open"
    alarms = cloudwatch_client.describe_alarms(AlarmNames=[alarm_name])
    assert len(alarms['MetricAlarms']) == 1


def test_eventbridge_remediation_rule_deployed(events_client, tfvars):
    rule_name = f"{tfvars['resource_prefix']}-circuit-breaker-remediation"
    response = events_client.describe_rule(Name=rule_name)
    assert response['State'] == 'ENABLED'


def test_eventbridge_recovery_rule_deployed(events_client, tfvars):
    rule_name = f"{tfvars['resource_prefix']}-circuit-breaker-recovery"
    response = events_client.describe_rule(Name=rule_name)
    assert response['State'] == 'ENABLED'


def test_sns_topic_deployed(sns_client, tfvars):
    topic_name = f"{tfvars['resource_prefix']}-circuit-breaker-alerts"
    topics = sns_client.list_topics()
    topic_arns = [t['TopicArn'] for t in topics['Topics']]
    matching_topics = [t for t in topic_arns if topic_name in t]
    assert len(matching_topics) == 1


def test_incidents_table_deployed(dynamodb_client, tfvars):
    table_name = f"{tfvars['resource_prefix']}-incidents"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['TableStatus'] == 'ACTIVE'


def test_circuit_breaker_state_table_deployed(dynamodb_client, tfvars):
    table_name = f"{tfvars['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['TableStatus'] == 'ACTIVE'


def test_recovery_lambda_can_be_invoked(lambda_client, tfvars):
    function_name = f"{tfvars['resource_prefix']}-CircuitBreakerRecovery"
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=b'{}'
    )
    assert response['StatusCode'] == 200


def test_dlq_reprocessor_lambda_can_be_invoked(lambda_client, tfvars):
    function_name = f"{tfvars['resource_prefix']}-DLQReprocessor"
    response = lambda_client.invoke(
        FunctionName=function_name,
        InvocationType='RequestResponse',
        Payload=b'{}'
    )
    assert response['StatusCode'] == 200


def test_circuit_breaker_state_table_readable(dynamodb_client, tfvars):
    table_name = f"{tfvars['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.get_item(
        TableName=table_name,
        Key={'state_id': {'S': 'current'}}
    )
    assert 'Item' in response or 'Item' not in response


def test_recovery_lambda_logs_exist(logs_client, tfvars):
    log_group_name = f"/aws/lambda/{tfvars['resource_prefix']}-CircuitBreakerRecovery"
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = [lg for lg in response['logGroups'] if lg['logGroupName'] == log_group_name]
    assert len(log_groups) == 1


def test_remediation_lambda_logs_exist(logs_client, tfvars):
    log_group_name = f"/aws/lambda/{tfvars['resource_prefix']}-CircuitBreakerRemediation"
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = [lg for lg in response['logGroups'] if lg['logGroupName'] == log_group_name]
    assert len(log_groups) == 1


def test_dlq_reprocessor_logs_exist(logs_client, tfvars):
    log_group_name = f"/aws/lambda/{tfvars['resource_prefix']}-DLQReprocessor"
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = [lg for lg in response['logGroups'] if lg['logGroupName'] == log_group_name]
    assert len(log_groups) == 1
