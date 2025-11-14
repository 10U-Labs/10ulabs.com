import json
import boto3
from pathlib import Path
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent.parent / 'src' / 'auth_between_aws_and_github' / 'config.json'
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def iam_client(config):
    return boto3.client('iam', region_name=config['aws']['region'])


class TestDeployedOIDCProvider:

    def test_oidc_provider_exists_in_aws(self, iam_client, config):
        account_id = config['aws']['account_id']
        provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"

        response = iam_client.get_open_id_connect_provider(
            OpenIDConnectProviderArn=provider_arn
        )

        assert response['Url'] == 'https://token.actions.githubusercontent.com'

    def test_oidc_provider_has_correct_thumbprint(self, iam_client, config):
        account_id = config['aws']['account_id']
        provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"

        response = iam_client.get_open_id_connect_provider(
            OpenIDConnectProviderArn=provider_arn
        )

        assert '6938fd4d98bab03faadb97b34396831e3780aea1' in response['ThumbprintList']

    def test_oidc_provider_has_correct_client_id(self, iam_client, config):
        account_id = config['aws']['account_id']
        provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"

        response = iam_client.get_open_id_connect_provider(
            OpenIDConnectProviderArn=provider_arn
        )

        assert 'sts.amazonaws.com' in response['ClientIDList']


class TestDeployedIAMRole:

    def test_iam_role_exists_in_aws(self, iam_client, config):
        role_name = config['aws']['iam_role_name']

        response = iam_client.get_role(RoleName=role_name)

        assert response['Role']['RoleName'] == role_name

    def test_iam_role_trust_policy_has_federated_principal(self, iam_client, config):
        role_name = config['aws']['iam_role_name']
        account_id = config['aws']['account_id']
        expected_provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"

        response = iam_client.get_role(RoleName=role_name)
        trust_policy = response['Role']['AssumeRolePolicyDocument']

        federated_principals = [
            stmt['Principal'].get('Federated')
            for stmt in trust_policy['Statement']
            if 'Federated' in stmt.get('Principal', {})
        ]

        assert expected_provider_arn in federated_principals

    def test_iam_role_trust_policy_has_correct_audience_condition(self, iam_client, config):
        role_name = config['aws']['iam_role_name']

        response = iam_client.get_role(RoleName=role_name)
        trust_policy = response['Role']['AssumeRolePolicyDocument']

        has_aud_condition = False
        for stmt in trust_policy['Statement']:
            condition = stmt.get('Condition', {})
            string_equals = condition.get('StringEquals', {})
            if 'token.actions.githubusercontent.com:aud' in string_equals:
                assert string_equals['token.actions.githubusercontent.com:aud'] == 'sts.amazonaws.com'
                has_aud_condition = True

        assert has_aud_condition

    def test_iam_role_trust_policy_has_correct_subject_condition(self, iam_client, config):
        role_name = config['aws']['iam_role_name']
        github_org = config['github']['org']
        github_repo = config['github']['repo']
        expected_pattern = f"repo:{github_org}/{github_repo}:*"

        response = iam_client.get_role(RoleName=role_name)
        trust_policy = response['Role']['AssumeRolePolicyDocument']

        has_sub_condition = False
        for stmt in trust_policy['Statement']:
            condition = stmt.get('Condition', {})
            string_like = condition.get('StringLike', {})
            if 'token.actions.githubusercontent.com:sub' in string_like:
                assert string_like['token.actions.githubusercontent.com:sub'] == expected_pattern
                has_sub_condition = True

        assert has_sub_condition

    def test_iam_role_has_administrator_access_policy(self, iam_client, config):
        role_name = config['aws']['iam_role_name']

        response = iam_client.list_attached_role_policies(RoleName=role_name)

        policy_arns = [p['PolicyArn'] for p in response['AttachedPolicies']]
        assert 'arn:aws:iam::aws:policy/AdministratorAccess' in policy_arns
