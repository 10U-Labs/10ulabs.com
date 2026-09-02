import json
import os
import subprocess
import urllib.request
from typing import Any, Dict
import pytest


def get_github_oidc_token() -> str:
    token_url = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_URL')
    token_request_token = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_TOKEN')
    if not token_url or not token_request_token:
        pytest.skip("OIDC token not available")
    url = f'{token_url}&audience=sts.amazonaws.com'
    request = urllib.request.Request(
        url,
        headers={'Authorization': f'Bearer {token_request_token}'}
    )
    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode('utf-8'))
    token = data.get('value')
    if not token:
        pytest.fail("Could not retrieve OIDC token")
    return token


def assume_role_with_oidc(
    account_id: str,
    region: str,
    role_name: str,
    oidc_token: str
) -> Dict[str, str]:
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    result = subprocess.run(
        ['aws', 'sts', 'assume-role-with-web-identity',
         '--role-arn', role_arn,
         '--role-session-name', 'e2e-test-session',
         '--web-identity-token', oidc_token,
         '--region', region,
         '--output', 'json'],
        capture_output=True,
        text=True,
        check=True
    )
    data = json.loads(result.stdout)
    creds = data['Credentials']
    return {
        'access_key_id': creds['AccessKeyId'],
        'secret_access_key': creds['SecretAccessKey'],
        'session_token': creds['SessionToken']
    }


def get_caller_identity_arn(aws_creds: Any, region: str) -> str:
    env = os.environ.copy()
    env['AWS_ACCESS_KEY_ID'] = aws_creds['access_key_id']
    env['AWS_SECRET_ACCESS_KEY'] = aws_creds['secret_access_key']
    env['AWS_SESSION_TOKEN'] = aws_creds['session_token']
    result = subprocess.run(
        ['aws', 'sts', 'get-caller-identity',
         '--region', region,
         '--output', 'json'],
        capture_output=True,
        text=True,
        check=True,
        env=env
    )
    identity = json.loads(result.stdout)
    return identity['Arn']


class TestCompleteOIDCWorkflow:
    @pytest.fixture
    def oidc_token(self) -> str:
        return get_github_oidc_token()

    @pytest.fixture
    def aws_creds(
        self,
        config: Dict[str, Any],
        oidc_token: str,
        aws_account_id: str
    ) -> Dict[str, str]:
        return assume_role_with_oidc(
            aws_account_id,
            config['aws_region'],
            config['name_for_github_actions_role'],
            oidc_token
        )

    @pytest.fixture
    def caller_arn(self, config: Dict[str, Any], aws_creds: Any) -> str:
        return get_caller_identity_arn(aws_creds, config['aws_region'])


    def test_oidc_token_is_not_none(self, oidc_token: str) -> None:
        assert oidc_token is not None

    def test_oidc_token_is_not_empty(self, oidc_token: str) -> None:
        assert len(oidc_token) > 0


    def test_aws_credentials_has_access_key_id(self, aws_creds: Any) -> None:
        assert aws_creds['access_key_id'] is not None

    def test_aws_credentials_has_secret_access_key(self, aws_creds: Any) -> None:
        assert aws_creds['secret_access_key'] is not None

    def test_aws_credentials_has_session_token(self, aws_creds: Any) -> None:
        assert aws_creds['session_token'] is not None


    def test_assumed_role_arn_contains_role_name(
        self,
        config: Dict[str, Any],
        caller_arn: str
    ) -> None:
        role_name = config['name_for_github_actions_role']
        assert role_name in caller_arn

    def test_assumed_role_arn_contains_assumed_role_prefix(self, caller_arn: str) -> None:
        assert 'assumed-role' in caller_arn
