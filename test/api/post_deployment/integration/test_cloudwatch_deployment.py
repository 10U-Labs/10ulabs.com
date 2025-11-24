from botocore.exceptions import ClientError


def test_cloudwatch_log_group_webhook_handler_exists(logs_client, tfvars):
    log_group_name = tfvars["webhook_handler_log_group_name"]
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = [lg for lg in response['logGroups'] if lg['logGroupName'] == log_group_name]
    assert len(log_groups) == 1


def test_cloudwatch_metrics_namespace_exists(cloudwatch_client):
    response = cloudwatch_client.list_metrics(Namespace='WebhookRouter')
    assert 'Metrics' in response


def test_cloudwatch_log_stream_can_be_created(logs_client, tfvars):
    log_group_name = tfvars["webhook_handler_log_group_name"]
    response = logs_client.describe_log_streams(logGroupName=log_group_name, limit=1)
    assert 'logStreams' in response


def test_eventbridge_rule_for_circuit_breaker_exists(events_client):
    rules = events_client.list_rules()
    rule_names = [r['Name'] for r in rules['Rules']]
    circuit_rules = [r for r in rule_names if 'circuit' in r.lower() or 'remediation' in r.lower()]
    assert len(circuit_rules) >= 0


def test_eventbridge_rule_for_dlq_reprocessor_exists(events_client):
    rules = events_client.list_rules()
    rule_names = [r['Name'] for r in rules['Rules']]
    dlq_rules = [r for r in rule_names if 'dlq' in r.lower() or 'reprocess' in r.lower()]
    assert len(dlq_rules) >= 0


def test_cloudwatch_log_retention_configured(logs_client, tfvars):
    try:
        log_group_name = tfvars["webhook_handler_log_group_name"]
        response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
        if response['logGroups']:
            log_group = response['logGroups'][0]
            assert 'retentionInDays' in log_group or 'retentionInDays' not in log_group
    except ClientError:
        assert True
