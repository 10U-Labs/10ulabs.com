"""Post-deployment wiring tests for drift_recoveries endpoint.

Layer 3: Verify all components are connected properly.
These tests run after existence and configuration tests pass.
"""


# === EventBridge to Lambda Wiring ===


def test_eventbridge_rule_targets_lambda(events_client, cfg, function_name):
    """Verify EventBridge scheduled rule targets Lambda function."""
    rule_name = f"{cfg['resource_prefix']}-scheduled-check"
    response = events_client.list_targets_by_rule(Rule=rule_name)
    targets = response.get("Targets", [])
    target_arns = [t["Arn"] for t in targets]
    assert any(function_name in arn for arn in target_arns)


def test_lambda_has_eventbridge_permission(lambda_client, function_name):
    """Verify Lambda has permission for EventBridge invocation."""
    response = lambda_client.get_policy(FunctionName=function_name)
    policy = response["Policy"]
    assert "events.amazonaws.com" in policy


# === IAM Role Wiring ===


def test_lambda_role_has_sns_permissions(lambda_inline_policies):
    """Verify Lambda role has SNS permissions."""
    assert "SNSAccess" in lambda_inline_policies


def test_lambda_role_has_ssm_permissions(lambda_inline_policies):
    """Verify Lambda role has SSM permissions."""
    assert "SSMAccess" in lambda_inline_policies


def test_lambda_role_has_ec2_permissions(lambda_inline_policies):
    """Verify Lambda role has EC2 permissions."""
    assert "EC2Access" in lambda_inline_policies


def test_lambda_role_has_kms_permissions(lambda_inline_policies):
    """Verify Lambda role has KMS permissions."""
    assert "KMSAccess" in lambda_inline_policies


def test_lambda_role_has_basic_execution(iam_client, lambda_role_name):
    """Verify Lambda role has basic execution policy attached."""
    response = iam_client.list_attached_role_policies(RoleName=lambda_role_name)
    attached_arns = [p["PolicyArn"] for p in response.get("AttachedPolicies", [])]

    assert any("AWSLambdaBasicExecutionRole" in arn for arn in attached_arns)
