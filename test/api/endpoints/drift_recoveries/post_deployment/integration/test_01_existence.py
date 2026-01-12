"""Post-deployment existence tests for drift_recoveries endpoint.

Layer 1: Verify all deployed resources exist.
These tests run first to catch deployment failures before checking configuration.
"""


# === Lambda Functions ===


def test_lambda_function_exists(lambda_client, function_name):
    """Verify DriftRecoveries Lambda function exists."""
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


# === CloudWatch Log Groups ===


def test_lambda_log_group_exists(logs_client, function_name):
    """Verify Lambda CloudWatch log group exists."""
    log_group_name = f"/aws/lambda/{function_name}"
    response = logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
    log_groups = response.get("logGroups", [])
    assert any(lg["logGroupName"] == log_group_name for lg in log_groups)


# === SQS Queues ===


def test_sqs_queue_exists(sqs_client, queue_name):
    """Verify main SQS queue exists."""
    response = sqs_client.get_queue_url(QueueName=f"{queue_name}.fifo")
    assert queue_name in response["QueueUrl"]


def test_dlq_queue_exists(sqs_client, queue_name):
    """Verify DLQ SQS queue exists."""
    dlq_name = f"{queue_name}DLQ.fifo"
    response = sqs_client.get_queue_url(QueueName=dlq_name)
    assert "DLQ" in response["QueueUrl"]


# === SNS Topics ===


def test_sns_alerts_topic_exists(sns_client, cfg):
    """Verify SNS alerts topic exists."""
    topic_name = f"{cfg['resource_prefix']}-drift-recovery-alerts"
    response = sns_client.list_topics()
    topic_arns = [t["TopicArn"] for t in response.get("Topics", [])]
    assert any(topic_name in arn for arn in topic_arns)


# === S3 Buckets ===


def test_config_s3_bucket_exists(s3_client, cfg):
    """Verify Config S3 bucket exists."""
    bucket_prefix = f"{cfg['resource_prefix'].lower()}-config-"
    response = s3_client.list_buckets()
    bucket_names = [b["Name"] for b in response.get("Buckets", [])]
    assert any(name.startswith(bucket_prefix) for name in bucket_names)


# === AWS Config Resources ===


def test_config_recorder_exists(config_client, cfg):
    """Verify AWS Config recorder exists."""
    recorder_name = f"{cfg['resource_prefix']}-recorder"
    response = config_client.describe_configuration_recorders()
    recorders = response.get("ConfigurationRecorders", [])
    assert any(r["name"] == recorder_name for r in recorders)


def test_config_rule_exists(config_client, cfg):
    """Verify required-tags Config rule exists."""
    rule_name = f"{cfg['resource_prefix']}-required-tags"
    response = config_client.describe_config_rules(ConfigRuleNames=[rule_name])
    rules = response.get("ConfigRules", [])
    assert len(rules) == 1


# === EventBridge Rules ===


def test_eventbridge_rule_exists(events_client, cfg):
    """Verify EventBridge rule for config compliance changes exists."""
    rule_name = f"{cfg['resource_prefix']}-config-compliance-change"
    response = events_client.describe_rule(Name=rule_name)
    assert response["Name"] == rule_name


# === IAM Roles ===


def test_lambda_iam_role_exists(iam_client, cfg):
    """Verify Lambda IAM role exists."""
    role_name = f"{cfg['resource_prefix']}DriftRecoveriesRole"
    response = iam_client.get_role(RoleName=role_name)
    assert response["Role"]["RoleName"] == role_name


def test_config_recorder_iam_role_exists(iam_client, cfg):
    """Verify Config recorder IAM role exists."""
    role_name = f"{cfg['resource_prefix']}ConfigRecorderRole"
    response = iam_client.get_role(RoleName=role_name)
    assert response["Role"]["RoleName"] == role_name
