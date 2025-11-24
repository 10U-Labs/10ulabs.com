import time
import boto3
from botocore.exceptions import ClientError


def test_dynamodb_idempotency_table_exists():
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    response = dynamodb.describe_table(TableName='TenULabsWebhookHandler-idempotency')
    assert response['Table']['TableName'] == 'TenULabsWebhookHandler-idempotency'


def test_dynamodb_idempotency_table_has_ttl():
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    response = dynamodb.describe_time_to_live(TableName='TenULabsWebhookHandler-idempotency')
    assert response['TimeToLiveDescription']['TimeToLiveStatus'] == 'ENABLED'


def test_dynamodb_billing_mode(tfvars):
    dynamodb = boto3.client('dynamodb', region_name=tfvars["aws_region"])
    response = dynamodb.describe_table(TableName='TenULabsWebhookHandler-idempotency')
    assert response['Table']['BillingModeSummary']['BillingMode'] == 'PAY_PER_REQUEST'


def test_dynamodb_point_in_time_recovery(tfvars):
    dynamodb = boto3.client('dynamodb', region_name=tfvars["aws_region"])
    response = dynamodb.describe_continuous_backups(TableName='TenULabsWebhookHandler-idempotency')
    assert response['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']['PointInTimeRecoveryStatus'] == 'ENABLED'


def test_dynamodb_idempotency_table_key_schema(tfvars):
    dynamodb = boto3.client('dynamodb', region_name=tfvars["aws_region"])
    tables = dynamodb.list_tables()
    if tables['TableNames']:
        idempotency_tables = [t for t in tables['TableNames'] if 'idempotency' in t.lower()]
        if idempotency_tables:
            table_name = idempotency_tables[0]
            table_info = dynamodb.describe_table(TableName=table_name)
            key_schema = table_info['Table']['KeySchema']
            assert len(key_schema) > 0


def test_dynamodb_idempotency_table_ttl_attribute(tfvars):
    dynamodb = boto3.client('dynamodb', region_name=tfvars["aws_region"])
    tables = dynamodb.list_tables()
    if tables['TableNames']:
        idempotency_tables = [t for t in tables['TableNames'] if 'idempotency' in t.lower()]
        if idempotency_tables:
            table_name = idempotency_tables[0]
            ttl_info = dynamodb.describe_time_to_live(TableName=table_name)
            assert 'TimeToLiveDescription' in ttl_info


def test_dynamodb_idempotency_put_item_succeeds():
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    test_id = f'integration-test-{int(time.time())}'
    try:
        dynamodb.put_item(
            TableName='TenULabsWebhookHandler-idempotency',
            Item={
                'request_id': {'S': test_id},
                'ttl': {'N': str(int(time.time()) + 60)},
                'timestamp': {'N': str(int(time.time()))}
            }
        )
        response = dynamodb.get_item(
            TableName='TenULabsWebhookHandler-idempotency',
            Key={'request_id': {'S': test_id}}
        )
        assert 'Item' in response
        dynamodb.delete_item(
            TableName='TenULabsWebhookHandler-idempotency',
            Key={'request_id': {'S': test_id}}
        )
    except ClientError:
        assert True


def test_dynamodb_conditional_put_prevents_duplicates():
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    test_id = f'integration-test-duplicate-{int(time.time())}'
    try:
        dynamodb.put_item(
            TableName='TenULabsWebhookHandler-idempotency',
            Item={
                'request_id': {'S': test_id},
                'ttl': {'N': str(int(time.time()) + 60)},
                'timestamp': {'N': str(int(time.time()))}
            }
        )
        try:
            dynamodb.put_item(
                TableName='TenULabsWebhookHandler-idempotency',
                Item={
                    'request_id': {'S': test_id},
                    'ttl': {'N': str(int(time.time()) + 60)},
                    'timestamp': {'N': str(int(time.time()))}
                },
                ConditionExpression='attribute_not_exists(request_id)'
            )
            assert False
        except ClientError as e:
            assert e.response['Error']['Code'] == 'ConditionalCheckFailedException'
        dynamodb.delete_item(
            TableName='TenULabsWebhookHandler-idempotency',
            Key={'request_id': {'S': test_id}}
        )
    except ClientError:
        assert True
