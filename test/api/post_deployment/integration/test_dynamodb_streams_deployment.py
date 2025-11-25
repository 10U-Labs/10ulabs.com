def test_circuit_breaker_state_table_has_stream_enabled(dynamodb_client):
    response = dynamodb_client.describe_table(TableName='TenULabs-circuit-breaker-state')
    stream_spec = response['Table'].get('StreamSpecification', {})
    assert stream_spec.get('StreamEnabled') is True


def test_circuit_breaker_state_table_stream_view_type_is_new_and_old_images(dynamodb_client):
    response = dynamodb_client.describe_table(TableName='TenULabs-circuit-breaker-state')
    stream_spec = response['Table'].get('StreamSpecification', {})
    assert stream_spec.get('StreamViewType') == 'NEW_AND_OLD_IMAGES'


def test_circuit_breaker_state_table_has_stream_arn(dynamodb_client):
    response = dynamodb_client.describe_table(TableName='TenULabs-circuit-breaker-state')
    stream_arn = response['Table'].get('LatestStreamArn')
    assert stream_arn is not None


def test_idempotency_table_does_not_have_stream_enabled(dynamodb_client, config):
    table_name = config['idempotency_table_name']
    response = dynamodb_client.describe_table(TableName=table_name)
    stream_spec = response['Table'].get('StreamSpecification', {})
    assert stream_spec.get('StreamEnabled', False) is False
