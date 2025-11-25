def test_iam_role_exists_in_aws(iam_client, config):
    role_name = config['name_for_github_actions_role']
    response = iam_client.get_role(RoleName=role_name)
    assert response['Role']['RoleName'] == role_name


def test_iam_role_trust_policy_has_federated_principal(iam_client, config):
    role_name = config['name_for_github_actions_role']
    account_id = config['aws_account_id']
    expected_provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    federated_principal = trust_policy['Statement'][0]['Principal']['Federated']
    assert expected_provider_arn == federated_principal


def test_iam_role_trust_policy_has_correct_audience_condition(iam_client, config):
    role_name = config['name_for_github_actions_role']
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    condition = trust_policy['Statement'][0]['Condition']
    string_equals = condition['StringEquals']
    aud_value = string_equals['token.actions.githubusercontent.com:aud']
    assert aud_value == 'sts.amazonaws.com'


def test_iam_role_trust_policy_has_correct_subject_condition(iam_client, config):
    role_name = config['name_for_github_actions_role']
    github_org = config['github_org']
    github_repo = config['name_for_github_repo']
    expected_pattern = f"repo:{github_org}/{github_repo}:*"
    response = iam_client.get_role(RoleName=role_name)
    trust_policy = response['Role']['AssumeRolePolicyDocument']
    condition = trust_policy['Statement'][0]['Condition']
    string_like = condition['StringLike']
    sub_value = string_like['token.actions.githubusercontent.com:sub']
    assert sub_value == expected_pattern


def test_iam_role_has_administrator_access_policy(iam_client, config):
    role_name = config['name_for_github_actions_role']
    response = iam_client.list_attached_role_policies(RoleName=role_name)
    policy_arn = response['AttachedPolicies'][0]['PolicyArn']
    assert policy_arn == 'arn:aws:iam::aws:policy/AdministratorAccess'
