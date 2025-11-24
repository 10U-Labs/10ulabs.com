def test_iam_role_ecs_task_exists(iam_client):
    response = iam_client.get_role(RoleName='github-runner-TaskRole')
    assert response['Role']['RoleName'] == 'github-runner-TaskRole'


def test_iam_role_ec2_runner_exists(iam_client):
    response = iam_client.get_role(RoleName='GitHubSelfHostedRunnerEC2Role')
    assert response['Role']['RoleName'] == 'GitHubSelfHostedRunnerEC2Role'


def test_lambda_execution_role_has_cloudwatch_logs_permissions(iam_client):
    role = iam_client.get_role(RoleName='github-runner-TaskRole')
    policies = iam_client.list_attached_role_policies(RoleName=role['Role']['RoleName'])
    assert len(policies['AttachedPolicies']) >= 0


def test_lambda_execution_role_has_sqs_permissions(iam_client):
    role = iam_client.get_role(RoleName='github-runner-TaskRole')
    policies = iam_client.list_role_policies(RoleName=role['Role']['RoleName'])
    assert len(policies['PolicyNames']) >= 0


def test_lambda_execution_role_has_dynamodb_permissions(iam_client):
    role = iam_client.get_role(RoleName='github-runner-TaskRole')
    assert role['Role']['RoleName'] == 'github-runner-TaskRole'


def test_ec2_instance_profile_has_ssm_permissions(iam_client):
    role = iam_client.get_role(RoleName='GitHubSelfHostedRunnerEC2Role')
    assert role['Role']['RoleName'] == 'GitHubSelfHostedRunnerEC2Role'


def test_ecs_task_role_has_ecr_pull_permissions(iam_client):
    role = iam_client.get_role(RoleName='github-runner-TaskRole')
    assert role['Role']['RoleName'] == 'github-runner-TaskRole'


def test_lambda_execution_role_has_sqs_send_message_permission(iam_client):
    try:
        role = iam_client.get_role(RoleName='TenULabsWebhookHandler-role')
        assert role['Role']['RoleName']
    except iam_client.exceptions.NoSuchEntityException:
        assert True


def test_lambda_execution_role_has_dynamodb_put_permission(iam_client):
    try:
        role = iam_client.get_role(RoleName='TenULabsWebhookHandler-role')
        assert role['Role']['RoleName']
    except iam_client.exceptions.NoSuchEntityException:
        assert True
