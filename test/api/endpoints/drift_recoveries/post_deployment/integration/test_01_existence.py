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


# === SNS Topics ===


def test_sns_alerts_topic_exists(sns_client, cfg):
    """Verify SNS alerts topic exists."""
    topic_name = f"{cfg['resource_prefix']}-drift-recovery-alerts"
    response = sns_client.list_topics()
    topic_arns = [t["TopicArn"] for t in response.get("Topics", [])]
    assert any(topic_name in arn for arn in topic_arns)


# === EventBridge Rules ===


def test_eventbridge_scheduled_rule_exists(events_client, cfg):
    """Verify EventBridge scheduled rule exists."""
    rule_name = f"{cfg['resource_prefix']}-scheduled-check"
    response = events_client.describe_rule(Name=rule_name)
    assert response["Name"] == rule_name


# === IAM Roles ===


def test_lambda_iam_role_exists(iam_client, cfg):
    """Verify Lambda IAM role exists."""
    role_name = f"{cfg['resource_prefix']}DriftRecoveriesRole"
    response = iam_client.get_role(RoleName=role_name)
    assert response["Role"]["RoleName"] == role_name
