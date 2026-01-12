"""Post-deployment wiring tests for drift_recoveries endpoint.

Layer 3: Verify all components are connected properly.
These tests run after existence and configuration tests pass.
"""


# === Lambda Event Source Mapping ===


def test_lambda_has_sqs_trigger(lambda_client, function_name, queue_name):
    """Verify Lambda has SQS queue as event source."""
    response = lambda_client.list_event_source_mappings(
        FunctionName=function_name
    )
    mappings = response.get("EventSourceMappings", [])
    source_arns = [m["EventSourceArn"] for m in mappings]
    assert any(queue_name in arn for arn in source_arns)


def test_lambda_sqs_trigger_is_enabled(lambda_client, function_name, queue_name):
    """Verify Lambda SQS event source mapping is enabled."""
    response = lambda_client.list_event_source_mappings(
        FunctionName=function_name
    )
    mappings = response.get("EventSourceMappings", [])
    sqs_mapping = next((m for m in mappings if queue_name in m["EventSourceArn"]), None)
    assert sqs_mapping["State"] == "Enabled"


def test_lambda_sqs_trigger_batch_size_is_one(lambda_client, function_name, queue_name):
    """Verify Lambda SQS trigger batch size is 1."""
    response = lambda_client.list_event_source_mappings(
        FunctionName=function_name
    )
    mappings = response.get("EventSourceMappings", [])
    sqs_mapping = next((m for m in mappings if queue_name in m["EventSourceArn"]), None)
    assert sqs_mapping["BatchSize"] == 1


# === EventBridge to SQS Wiring ===


def test_eventbridge_targets_sqs_queue(events_client, cfg, queue_name):
    """Verify EventBridge rule targets SQS queue."""
    rule_name = f"{cfg['resource_prefix']}-config-compliance-change"
    response = events_client.list_targets_by_rule(Rule=rule_name)
    targets = response.get("Targets", [])
    target_arns = [t["Arn"] for t in targets]
    assert any(queue_name in arn for arn in target_arns)


# === SQS to DLQ Wiring ===


def test_sqs_queue_redrives_to_dlq(sqs_client, queue_name):
    """Verify main queue has redrive policy to DLQ."""
    queue_url = sqs_client.get_queue_url(QueueName=f"{queue_name}.fifo")["QueueUrl"]
    attrs = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=["RedrivePolicy"]
    )
    redrive_policy = attrs["Attributes"].get("RedrivePolicy", "{}")
    assert "DLQ" in redrive_policy


# === IAM Role Wiring ===


def test_lambda_role_has_sqs_permissions(lambda_client, iam_client, function_name):
    """Verify Lambda role has SQS permissions."""
    lambda_config = lambda_client.get_function(FunctionName=function_name)
    role_arn = lambda_config["Configuration"]["Role"]
    role_name = role_arn.split("/")[-1]

    inline_response = iam_client.list_role_policies(RoleName=role_name)
    inline_policies = inline_response.get("PolicyNames", [])

    assert "SQSAccess" in inline_policies


def test_lambda_role_has_sns_permissions(lambda_client, iam_client, function_name):
    """Verify Lambda role has SNS permissions."""
    lambda_config = lambda_client.get_function(FunctionName=function_name)
    role_arn = lambda_config["Configuration"]["Role"]
    role_name = role_arn.split("/")[-1]

    inline_response = iam_client.list_role_policies(RoleName=role_name)
    inline_policies = inline_response.get("PolicyNames", [])

    assert "SNSAccess" in inline_policies


def test_lambda_role_has_ssm_permissions(lambda_client, iam_client, function_name):
    """Verify Lambda role has SSM permissions."""
    lambda_config = lambda_client.get_function(FunctionName=function_name)
    role_arn = lambda_config["Configuration"]["Role"]
    role_name = role_arn.split("/")[-1]

    inline_response = iam_client.list_role_policies(RoleName=role_name)
    inline_policies = inline_response.get("PolicyNames", [])

    assert "SSMAccess" in inline_policies


def test_lambda_role_has_ec2_permissions(lambda_client, iam_client, function_name):
    """Verify Lambda role has EC2 permissions."""
    lambda_config = lambda_client.get_function(FunctionName=function_name)
    role_arn = lambda_config["Configuration"]["Role"]
    role_name = role_arn.split("/")[-1]

    inline_response = iam_client.list_role_policies(RoleName=role_name)
    inline_policies = inline_response.get("PolicyNames", [])

    assert "EC2Access" in inline_policies


def test_lambda_role_has_basic_execution(lambda_client, iam_client, function_name):
    """Verify Lambda role has basic execution policy attached."""
    lambda_config = lambda_client.get_function(FunctionName=function_name)
    role_arn = lambda_config["Configuration"]["Role"]
    role_name = role_arn.split("/")[-1]

    response = iam_client.list_attached_role_policies(RoleName=role_name)
    attached_arns = [p["PolicyArn"] for p in response.get("AttachedPolicies", [])]

    assert any("AWSLambdaBasicExecutionRole" in arn for arn in attached_arns)


# === Config Recorder Wiring ===


def test_config_recorder_uses_correct_role(config_client, cfg):
    """Verify Config recorder uses the correct IAM role."""
    recorder_name = f"{cfg['resource_prefix']}-recorder"
    response = config_client.describe_configuration_recorders()
    recorders = response.get("ConfigurationRecorders", [])
    recorder = next((r for r in recorders if r["name"] == recorder_name), None)
    role_arn = recorder["roleARN"]
    assert f"{cfg['resource_prefix']}ConfigRecorderRole" in role_arn


def test_config_delivery_channel_uses_correct_bucket(config_client, cfg):
    """Verify Config delivery channel uses the correct S3 bucket."""
    delivery_name = f"{cfg['resource_prefix']}-delivery"
    response = config_client.describe_delivery_channels()
    channels = response.get("DeliveryChannels", [])
    channel = next((c for c in channels if c["name"] == delivery_name), None)
    bucket_name = channel["s3BucketName"]
    assert cfg["resource_prefix"].lower() in bucket_name.lower()
