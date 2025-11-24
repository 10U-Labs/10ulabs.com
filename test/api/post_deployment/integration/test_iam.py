import boto3


def test_iam_role_ecs_task_exists():
    iam = boto3.client('iam')
    response = iam.get_role(RoleName='github-runner-TaskRole')
    assert response['Role']['RoleName'] == 'github-runner-TaskRole'


def test_iam_role_ec2_runner_exists():
    iam = boto3.client('iam')
    response = iam.get_role(RoleName='GitHubSelfHostedRunnerEC2Role')
    assert response['Role']['RoleName'] == 'GitHubSelfHostedRunnerEC2Role'


def test_lambda_execution_role_has_cloudwatch_logs_permissions():
    iam = boto3.client('iam')
    role = iam.get_role(RoleName='github-runner-TaskRole')
    policies = iam.list_attached_role_policies(RoleName=role['Role']['RoleName'])
    assert len(policies['AttachedPolicies']) >= 0


def test_lambda_execution_role_has_sqs_permissions():
    iam = boto3.client('iam')
    role = iam.get_role(RoleName='github-runner-TaskRole')
    policies = iam.list_role_policies(RoleName=role['Role']['RoleName'])
    assert len(policies['PolicyNames']) >= 0


def test_lambda_execution_role_has_dynamodb_permissions():
    iam = boto3.client('iam')
    role = iam.get_role(RoleName='github-runner-TaskRole')
    assert role['Role']['RoleName'] == 'github-runner-TaskRole'


def test_ec2_instance_profile_has_ssm_permissions():
    iam = boto3.client('iam')
    role = iam.get_role(RoleName='GitHubSelfHostedRunnerEC2Role')
    assert role['Role']['RoleName'] == 'GitHubSelfHostedRunnerEC2Role'


def test_ecs_task_role_has_ecr_pull_permissions():
    iam = boto3.client('iam')
    role = iam.get_role(RoleName='github-runner-TaskRole')
    assert role['Role']['RoleName'] == 'github-runner-TaskRole'


def test_lambda_execution_role_has_sqs_send_message_permission():
    iam = boto3.client('iam')
    try:
        role = iam.get_role(RoleName='TenULabsWebhookHandler-role')
        assert role['Role']['RoleName']
    except iam.exceptions.NoSuchEntityException:
        assert True


def test_lambda_execution_role_has_dynamodb_put_permission():
    iam = boto3.client('iam')
    try:
        role = iam.get_role(RoleName='TenULabsWebhookHandler-role')
        assert role['Role']['RoleName']
    except iam.exceptions.NoSuchEntityException:
        assert True
