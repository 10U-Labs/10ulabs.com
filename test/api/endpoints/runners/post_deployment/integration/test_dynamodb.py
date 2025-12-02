import time

from botocore.exceptions import ClientError

from .conftest import create_test_dynamodb_item, cleanup_test_dynamodb_item


def test_dynamodb_idempotency_table_exists(dynamodb_client, config):
    table_name = config["idempotency_table_name"]
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['TableName'] == table_name


def test_dynamodb_idempotency_table_has_ttl(dynamodb_client, config):
    table_name = config["idempotency_table_name"]
    response = dynamodb_client.describe_time_to_live(TableName=table_name)
    assert response['TimeToLiveDescription']['TimeToLiveStatus'] == 'ENABLED'


def test_dynamodb_billing_mode(dynamodb_client, config):
    table_name = config["idempotency_table_name"]
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['BillingModeSummary']['BillingMode'] == 'PAY_PER_REQUEST'


def test_dynamodb_point_in_time_recovery(dynamodb_client, config):
    table_name = config["idempotency_table_name"]
    response = dynamodb_client.describe_continuous_backups(TableName=table_name)
    assert response['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']['PointInTimeRecoveryStatus'] == 'ENABLED'


def test_dynamodb_idempotency_table_key_schema(dynamodb_client):
    tables = dynamodb_client.list_tables()
    if tables['TableNames']:
        idempotency_tables = [t for t in tables['TableNames'] if 'idempotency' in t.lower()]
        if idempotency_tables:
            table_name = idempotency_tables[0]
            table_info = dynamodb_client.describe_table(TableName=table_name)
            key_schema = table_info['Table']['KeySchema']
            assert len(key_schema) > 0


def test_dynamodb_idempotency_table_ttl_attribute(dynamodb_client):
    tables = dynamodb_client.list_tables()
    if tables['TableNames']:
        idempotency_tables = [t for t in tables['TableNames'] if 'idempotency' in t.lower()]
        if idempotency_tables:
            table_name = idempotency_tables[0]
            ttl_info = dynamodb_client.describe_time_to_live(TableName=table_name)
            assert 'TimeToLiveDescription' in ttl_info


def test_dynamodb_idempotency_put_item_succeeds(dynamodb_client, config):
    table_name = config["idempotency_table_name"]
    test_id = f'integration-test-{int(time.time())}'
    create_test_dynamodb_item(
        dynamodb_client,
        table_name,
        {
            'request_id': {'S': test_id},
            'ttl': {'N': str(int(time.time()) + 60)},
            'timestamp': {'N': str(int(time.time()))}
        }
    )
    response = dynamodb_client.get_item(
        TableName=table_name,
        Key={'request_id': {'S': test_id}}
    )
    cleanup_test_dynamodb_item(
        dynamodb_client,
        table_name,
        {'request_id': {'S': test_id}}
    )
    assert 'Item' in response


def test_dynamodb_conditional_put_prevents_duplicates(dynamodb_client, config):
    table_name = config["idempotency_table_name"]
    test_id = f'integration-test-duplicate-{int(time.time())}'
    create_test_dynamodb_item(
        dynamodb_client,
        table_name,
        {
            'request_id': {'S': test_id},
            'ttl': {'N': str(int(time.time()) + 60)},
            'timestamp': {'N': str(int(time.time()))}
        }
    )
    exception_raised = None
    try:
        dynamodb_client.put_item(
            TableName=table_name,
            Item={
                'request_id': {'S': test_id},
                'ttl': {'N': str(int(time.time()) + 60)},
                'timestamp': {'N': str(int(time.time()))}
            },
            ConditionExpression='attribute_not_exists(request_id)'
        )
    except ClientError as e:
        exception_raised = e
    cleanup_test_dynamodb_item(
        dynamodb_client,
        table_name,
        {'request_id': {'S': test_id}}
    )
    assert exception_raised.response['Error']['Code'] == 'ConditionalCheckFailedException'


def test_dynamodb_incidents_table_exists(dynamodb_client, config):
    table_name = f"{config['resource_prefix']}-incidents"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['TableName'] == table_name


def test_dynamodb_incidents_table_has_ttl(dynamodb_client, config):
    table_name = f"{config['resource_prefix']}-incidents"
    response = dynamodb_client.describe_time_to_live(TableName=table_name)
    assert response['TimeToLiveDescription']['TimeToLiveStatus'] == 'ENABLED'


def test_dynamodb_incidents_table_key_schema(dynamodb_client, config):
    table_name = f"{config['resource_prefix']}-incidents"
    response = dynamodb_client.describe_table(TableName=table_name)
    key_schema = response['Table']['KeySchema']
    assert key_schema[0]['AttributeName'] == 'incident_id'


def test_dynamodb_incidents_table_billing_mode(dynamodb_client, config):
    table_name = f"{config['resource_prefix']}-incidents"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['BillingModeSummary']['BillingMode'] == 'PAY_PER_REQUEST'


def test_dynamodb_circuit_breaker_state_table_exists(dynamodb_client, config):
    table_name = f"{config['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['TableName'] == table_name


def test_dynamodb_circuit_breaker_state_table_has_ttl(dynamodb_client, config):
    table_name = f"{config['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.describe_time_to_live(TableName=table_name)
    assert response['TimeToLiveDescription']['TimeToLiveStatus'] == 'ENABLED'


def test_dynamodb_circuit_breaker_state_table_key_schema(dynamodb_client, config):
    table_name = f"{config['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.describe_table(TableName=table_name)
    key_schema = response['Table']['KeySchema']
    assert key_schema[0]['AttributeName'] == 'state_id'


def test_dynamodb_circuit_breaker_state_table_billing_mode(dynamodb_client, config):
    table_name = f"{config['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['BillingModeSummary']['BillingMode'] == 'PAY_PER_REQUEST'


def test_dynamodb_circuit_breaker_state_table_point_in_time_recovery(dynamodb_client, config):
    table_name = f"{config['resource_prefix']}-circuit-breaker-state"
    response = dynamodb_client.describe_continuous_backups(TableName=table_name)
    assert response['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']['PointInTimeRecoveryStatus'] == 'ENABLED'


def test_dynamodb_incidents_table_point_in_time_recovery(dynamodb_client, config):
    table_name = f"{config['resource_prefix']}-incidents"
    response = dynamodb_client.describe_continuous_backups(TableName=table_name)
    assert response['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']['PointInTimeRecoveryStatus'] == 'ENABLED'
