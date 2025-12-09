"""Integration tests for AgentCore IAM role configuration."""


def _get_agentcore_role_name(config):
    """Get the AgentCore execution role name from config."""
    return f"{config['resource_prefix']}AgentCoreExecutionRole"


def test_agentcore_role_exists(iam_client, config):
    """Test that AgentCore IAM role exists in AWS."""
    role_name = _get_agentcore_role_name(config)
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


def test_agentcore_role_has_correct_trust_principal(iam_client, config):
    """Test that AgentCore role trusts bedrock-agentcore service."""
    role_name = _get_agentcore_role_name(config)
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    principal = trust_policy['Statement'][0]['Principal']['Service']
    assert principal == 'bedrock-agentcore.amazonaws.com'


def test_agentcore_role_has_assume_role_action(iam_client, config):
    """Test that AgentCore role allows sts:AssumeRole action."""
    role_name = _get_agentcore_role_name(config)
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    action = trust_policy['Statement'][0]['Action']
    assert action == 'sts:AssumeRole'


def test_agentcore_role_has_source_account_condition(iam_client, config):
    """Test that AgentCore role has aws:SourceAccount condition."""
    role_name = _get_agentcore_role_name(config)
    account_id = config['aws_account_id']
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    condition = trust_policy['Statement'][0]['Condition']
    source_account = condition['StringEquals']['aws:SourceAccount']
    assert source_account == account_id


def test_agentcore_role_has_source_arn_condition(iam_client, config):
    """Test that AgentCore role has aws:SourceArn condition."""
    role_name = _get_agentcore_role_name(config)
    account_id = config['aws_account_id']
    region = config['aws_region']
    expected_pattern = f"arn:aws:bedrock-agentcore:{region}:{account_id}:*"
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    condition = trust_policy['Statement'][0]['Condition']
    source_arn = condition['ArnLike']['aws:SourceArn']
    assert source_arn == expected_pattern


def test_agentcore_role_has_bedrock_managed_policy(iam_client, config):
    """Test that AgentCore role has BedrockAgentCoreFullAccess policy attached."""
    role_name = _get_agentcore_role_name(config)
    response = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arns = [p['PolicyArn'] for p in response['AttachedPolicies']]
    expected_policy = 'arn:aws:iam::aws:policy/BedrockAgentCoreFullAccess'
    assert expected_policy in policy_arns


def test_agentcore_role_has_inline_execution_policy(iam_client, config):
    """Test that AgentCore role has AgentCoreExecutionPolicy inline policy."""
    role_name = _get_agentcore_role_name(config)
    response = iam_client.list_role_policies(RoleName=role_name)
    policy_names = response['PolicyNames']
    assert 'AgentCoreExecutionPolicy' in policy_names


def test_agentcore_role_has_managed_by_tag(iam_client, config):
    """Test that AgentCore role has ManagedBy tag set to terraform."""
    role_name = _get_agentcore_role_name(config)
    response = iam_client.list_role_tags(RoleName=role_name)
    tags = {t['Key']: t['Value'] for t in response['Tags']}
    assert tags.get('ManagedBy') == 'terraform'


def test_agentcore_role_has_stack_tag(iam_client, config):
    """Test that AgentCore role has Stack tag set to bootstrap."""
    role_name = _get_agentcore_role_name(config)
    response = iam_client.list_role_tags(RoleName=role_name)
    tags = {t['Key']: t['Value'] for t in response['Tags']}
    assert tags.get('Stack') == 'bootstrap'


def test_agentcore_role_has_name_tag(iam_client, config):
    """Test that AgentCore role has Name tag matching role name."""
    role_name = _get_agentcore_role_name(config)
    response = iam_client.list_role_tags(RoleName=role_name)
    tags = {t['Key']: t['Value'] for t in response['Tags']}
    assert tags.get('Name') == role_name
