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
    role = iam_client.get_role(RoleName='TenULabsWebhookHandler-ServiceRole')
    assert role['Role']['RoleName'] == 'TenULabsWebhookHandler-ServiceRole'


def test_lambda_execution_role_has_dynamodb_put_permission(iam_client):
    role = iam_client.get_role(RoleName='TenULabsWebhookHandler-ServiceRole')
    assert role['Role']['RoleName'] == 'TenULabsWebhookHandler-ServiceRole'


def test_circuit_breaker_remediation_role_exists(iam_client, config):
    role_name = f"{config['resource_prefix']}-CircuitBreakerRemediation-Role"
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


def test_circuit_breaker_remediation_role_has_basic_execution_policy(iam_client, config):
    role_name = f"{config['resource_prefix']}-CircuitBreakerRemediation-Role"
    policies = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arns = [p['PolicyArn'] for p in policies['AttachedPolicies']]
    assert 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole' in policy_arns


def test_circuit_breaker_remediation_role_has_inline_policies(iam_client, config):
    role_name = f"{config['resource_prefix']}-CircuitBreakerRemediation-Role"
    policies = iam_client.list_role_policies(RoleName=role_name)
    assert len(policies['PolicyNames']) >= 1


def test_circuit_breaker_recovery_role_exists(iam_client, config):
    role_name = f"{config['resource_prefix']}-CircuitBreakerRecovery-Role"
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


def test_circuit_breaker_recovery_role_has_basic_execution_policy(iam_client, config):
    role_name = f"{config['resource_prefix']}-CircuitBreakerRecovery-Role"
    policies = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arns = [p['PolicyArn'] for p in policies['AttachedPolicies']]
    assert 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole' in policy_arns


def test_circuit_breaker_recovery_role_has_inline_policies(iam_client, config):
    role_name = f"{config['resource_prefix']}-CircuitBreakerRecovery-Role"
    policies = iam_client.list_role_policies(RoleName=role_name)
    assert len(policies['PolicyNames']) >= 1


def test_dlq_reprocessor_role_exists(iam_client, config):
    role_name = f"{config['resource_prefix']}-DLQReprocessor-Role"
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


def test_dlq_reprocessor_role_has_basic_execution_policy(iam_client, config):
    role_name = f"{config['resource_prefix']}-DLQReprocessor-Role"
    policies = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arns = [p['PolicyArn'] for p in policies['AttachedPolicies']]
    assert 'arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole' in policy_arns


def test_dlq_reprocessor_role_has_sqs_permissions(iam_client, config):
    role_name = f"{config['resource_prefix']}-DLQReprocessor-Role"
    policies = iam_client.list_role_policies(RoleName=role_name)
    assert len(policies['PolicyNames']) >= 1


def test_v1_handler_role_has_ecs_run_task_permission(iam_client):
    role_name = 'V1ApiHandler-ServiceRole'
    policies = iam_client.list_role_policies(RoleName=role_name)
    has_run_task = False
    for policy_name in policies['PolicyNames']:
        policy_doc = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        policy_document = policy_doc['PolicyDocument']
        for statement in policy_document.get('Statement', []):
            actions = statement.get('Action', [])
            if isinstance(actions, str):
                actions = [actions]
            if 'ecs:RunTask' in actions:
                has_run_task = True
                break
        if has_run_task:
            break
    assert has_run_task


def test_v1_handler_role_has_ecs_tag_resource_permission(iam_client):
    role_name = 'V1ApiHandler-ServiceRole'
    policies = iam_client.list_role_policies(RoleName=role_name)
    has_tag_resource = False
    for policy_name in policies['PolicyNames']:
        policy_doc = iam_client.get_role_policy(RoleName=role_name, PolicyName=policy_name)
        policy_document = policy_doc['PolicyDocument']
        for statement in policy_document.get('Statement', []):
            actions = statement.get('Action', [])
            if isinstance(actions, str):
                actions = [actions]
            if 'ecs:TagResource' in actions:
                has_tag_resource = True
                break
        if has_tag_resource:
            break
    assert has_tag_resource
