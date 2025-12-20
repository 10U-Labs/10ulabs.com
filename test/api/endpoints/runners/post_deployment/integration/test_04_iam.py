"""Post-deployment IAM tests for runners endpoint.

Layer 4: Verify IAM roles and policies are correctly configured and attached.
These tests ensure Lambda functions have the permissions they need.
"""


# === Lambda Role Attachment ===


def test_webhook_handler_uses_correct_role(lambda_client, config):
    """Verify webhook handler Lambda has the correct execution role attached."""
    function_name = config["webhook_handler_function_name"]
    role_name = config["webhook_handler_service_role_name"]
    account_id = config["aws_account_id"]

    response = lambda_client.get_function(FunctionName=function_name)
    actual_role_arn = response["Configuration"]["Role"]
    expected_role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

    assert actual_role_arn == expected_role_arn


# === Role Policy Permissions ===


def test_webhook_handler_role_has_sqs_get_queue_attributes(iam_client, config):
    """Verify webhook handler role has GetQueueAttributes permission on job queue.

    The webhook_router.py code calls get_queue_attributes on the job queue
    to publish queue depth metrics after enqueuing jobs.
    """
    role_name = config["webhook_handler_service_role_name"]

    # Get inline policies attached to the role
    policies = iam_client.list_role_policies(RoleName=role_name)

    found_permission = False
    for policy_name in policies["PolicyNames"]:
        policy = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        document = policy["PolicyDocument"]

        for statement in document.get("Statement", []):
            actions = statement.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            if "sqs:GetQueueAttributes" in actions:
                found_permission = True
                break

        if found_permission:
            break

    assert found_permission, (
        f"Role {role_name} missing sqs:GetQueueAttributes permission - "
        "webhook_router.py needs this to publish queue depth metrics"
    )


def test_webhook_handler_role_has_sqs_send_message(iam_client, config):
    """Verify webhook handler role has SendMessage permission."""
    role_name = config["webhook_handler_service_role_name"]

    policies = iam_client.list_role_policies(RoleName=role_name)

    found_permission = False
    for policy_name in policies["PolicyNames"]:
        policy = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        document = policy["PolicyDocument"]

        for statement in document.get("Statement", []):
            actions = statement.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            if "sqs:SendMessage" in actions:
                found_permission = True
                break

        if found_permission:
            break

    assert found_permission, f"Role {role_name} missing sqs:SendMessage permission"


def test_webhook_handler_role_has_dynamodb_access(iam_client, config):
    """Verify webhook handler role has DynamoDB access for idempotency."""
    role_name = config["webhook_handler_service_role_name"]

    policies = iam_client.list_role_policies(RoleName=role_name)

    found_permission = False
    for policy_name in policies["PolicyNames"]:
        policy = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        document = policy["PolicyDocument"]

        for statement in document.get("Statement", []):
            actions = statement.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            if "dynamodb:PutItem" in actions:
                found_permission = True
                break

        if found_permission:
            break

    assert found_permission, f"Role {role_name} missing dynamodb:PutItem permission"


def test_webhook_handler_role_has_ssm_access(iam_client, config):
    """Verify webhook handler role has SSM access for secrets."""
    role_name = config["webhook_handler_service_role_name"]

    policies = iam_client.list_role_policies(RoleName=role_name)

    found_permission = False
    for policy_name in policies["PolicyNames"]:
        policy = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        document = policy["PolicyDocument"]

        for statement in document.get("Statement", []):
            actions = statement.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            if "ssm:GetParameter" in actions:
                found_permission = True
                break

        if found_permission:
            break

    assert found_permission, f"Role {role_name} missing ssm:GetParameter permission"


def test_webhook_handler_role_has_cloudwatch_metrics(iam_client, config):
    """Verify webhook handler role has CloudWatch metrics permission."""
    role_name = config["webhook_handler_service_role_name"]

    policies = iam_client.list_role_policies(RoleName=role_name)

    found_permission = False
    for policy_name in policies["PolicyNames"]:
        policy = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        document = policy["PolicyDocument"]

        for statement in document.get("Statement", []):
            actions = statement.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            if "cloudwatch:PutMetricData" in actions:
                found_permission = True
                break

        if found_permission:
            break

    assert found_permission, f"Role {role_name} missing cloudwatch:PutMetricData permission"
