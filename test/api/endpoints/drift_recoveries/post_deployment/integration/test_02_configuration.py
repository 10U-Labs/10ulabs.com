"""Post-deployment configuration tests for drift_recoveries endpoint.

Layer 2: Verify all deployed resources are configured correctly.
These tests run after existence tests pass.
"""


# === Lambda Configuration ===


def test_lambda_runtime_is_python313(lambda_client, function_name):
    """Verify Lambda uses Python 3.13 runtime."""
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_architecture_is_arm64(lambda_client, function_name):
    """Verify Lambda uses arm64 architecture."""
    response = lambda_client.get_function(FunctionName=function_name)
    architectures = response["Configuration"].get("Architectures", [])
    assert "arm64" in architectures


def test_lambda_timeout_is_120_seconds(lambda_client, function_name):
    """Verify Lambda timeout is 120 seconds."""
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Timeout"] == 120


def test_lambda_memory_is_256mb(lambda_client, function_name):
    """Verify Lambda memory is 256 MB."""
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["MemorySize"] == 256


def test_lambda_has_github_repo_env_var(lambda_client, function_name):
    """Verify Lambda has GITHUB_REPO environment variable."""
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response["Configuration"].get("Environment", {}).get("Variables", {})
    assert "GITHUB_REPO" in env_vars


def test_lambda_has_github_token_parameter_name_env_var(lambda_client, function_name):
    """Verify Lambda has GITHUB_TOKEN_PARAMETER_NAME environment variable."""
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response["Configuration"].get("Environment", {}).get("Variables", {})
    assert "GITHUB_TOKEN_PARAMETER_NAME" in env_vars


def test_lambda_has_sns_topic_arn_env_var(lambda_client, function_name):
    """Verify Lambda has SNS_TOPIC_ARN environment variable."""
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response["Configuration"].get("Environment", {}).get("Variables", {})
    assert "SNS_TOPIC_ARN" in env_vars


def test_lambda_has_managed_vpc_id_env_var(lambda_client, function_name):
    """Verify Lambda has MANAGED_VPC_ID environment variable."""
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response["Configuration"].get("Environment", {}).get("Variables", {})
    assert "MANAGED_VPC_ID" in env_vars


# === CloudWatch Log Group Configuration ===


def test_lambda_log_group_has_30_day_retention(logs_client, function_name):
    """Verify Lambda log group has 30-day retention."""
    log_group_name = f"/aws/lambda/{function_name}"
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = response.get("logGroups", [])
    matching = [lg for lg in log_groups if lg["logGroupName"] == log_group_name]
    assert len(matching) == 1
    assert matching[0].get("retentionInDays") == 30


# === SQS Queue Configuration ===


def test_sqs_queue_is_fifo(sqs_client, queue_name):
    """Verify SQS queue is FIFO."""
    queue_url = sqs_client.get_queue_url(QueueName=f"{queue_name}.fifo")["QueueUrl"]
    attrs = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=["FifoQueue"]
    )
    assert attrs["Attributes"]["FifoQueue"] == "true"


def test_sqs_queue_has_300_second_visibility_timeout(sqs_client, queue_name):
    """Verify SQS queue has 300 second visibility timeout."""
    queue_url = sqs_client.get_queue_url(QueueName=f"{queue_name}.fifo")["QueueUrl"]
    attrs = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=["VisibilityTimeout"]
    )
    assert attrs["Attributes"]["VisibilityTimeout"] == "300"


def test_sqs_queue_has_1_day_retention(sqs_client, queue_name):
    """Verify SQS queue has 1-day message retention (86400 seconds)."""
    queue_url = sqs_client.get_queue_url(QueueName=f"{queue_name}.fifo")["QueueUrl"]
    attrs = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=["MessageRetentionPeriod"]
    )
    assert attrs["Attributes"]["MessageRetentionPeriod"] == "86400"


def test_dlq_has_14_day_retention(sqs_client, queue_name):
    """Verify DLQ has 14-day message retention (1209600 seconds)."""
    dlq_name = f"{queue_name}DLQ.fifo"
    queue_url = sqs_client.get_queue_url(QueueName=dlq_name)["QueueUrl"]
    attrs = sqs_client.get_queue_attributes(
        QueueUrl=queue_url,
        AttributeNames=["MessageRetentionPeriod"]
    )
    assert attrs["Attributes"]["MessageRetentionPeriod"] == "1209600"


# === AWS Config Configuration ===


def test_config_recorder_is_enabled(config_client, cfg):
    """Verify AWS Config recorder is enabled."""
    recorder_name = f"{cfg['resource_prefix']}-recorder"
    response = config_client.describe_configuration_recorder_status(
        ConfigurationRecorderNames=[recorder_name]
    )
    statuses = response.get("ConfigurationRecordersStatus", [])
    assert len(statuses) == 1
    assert statuses[0]["recording"] is True


def test_config_recorder_records_security_groups(config_client, cfg):
    """Verify Config recorder records EC2 security groups."""
    recorder_name = f"{cfg['resource_prefix']}-recorder"
    response = config_client.describe_configuration_recorders()
    recorders = response.get("ConfigurationRecorders", [])
    recorder = next((r for r in recorders if r["name"] == recorder_name), None)
    resource_types = recorder["recordingGroup"].get("resourceTypes", [])
    assert "AWS::EC2::SecurityGroup" in resource_types


def test_config_rule_checks_required_tags(config_client, cfg):
    """Verify Config rule checks for required tags."""
    rule_name = f"{cfg['resource_prefix']}-required-tags"
    response = config_client.describe_config_rules(ConfigRuleNames=[rule_name])
    rules = response.get("ConfigRules", [])
    assert len(rules) == 1
    assert rules[0]["Source"]["SourceIdentifier"] == "REQUIRED_TAGS"


# === EventBridge Configuration ===


def test_eventbridge_rule_is_enabled(events_client, cfg):
    """Verify EventBridge rule is enabled."""
    rule_name = f"{cfg['resource_prefix']}-config-compliance-change"
    response = events_client.describe_rule(Name=rule_name)
    assert response["State"] == "ENABLED"
