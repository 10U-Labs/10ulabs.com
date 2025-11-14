import json
import os
import subprocess

import pytest

from conftest import load_config


def get_github_oidc_token():
    token_url = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_URL')
    token_request_token = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_TOKEN')

    if not token_url or not token_request_token:
        pytest.skip("OIDC token not available (not in GitHub Actions with id-token: write)")

    result = subprocess.run(
        ['curl', '-s', '-H', f'Authorization: Bearer {token_request_token}',
         f'{token_url}&audience=sts.amazonaws.com'],
        capture_output=True,
        text=True,
        check=True
    )

    data = json.loads(result.stdout)
    token = data.get('value')

    if not token:
        pytest.fail("Could not retrieve OIDC token from GitHub Actions")

    return token


def assume_role_with_oidc(account_id, region, role_name, oidc_token):
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


class TestCompleteOIDCWorkflow:

    @pytest.fixture
    def config(self):
        return load_config()

    @pytest.fixture
    def oidc_token(self):
        return get_github_oidc_token()

    @pytest.fixture
    def aws_creds(self, config, oidc_token):
        return assume_role_with_oidc(
            config['aws']['account_id'],
            config['aws']['region'],
            config['aws']['iam_role_name'],
            oidc_token
        )

    @pytest.fixture
    def github_pat(self, config, aws_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = aws_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = aws_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = aws_creds['session_token']

        result = subprocess.run(
            ['aws', 'secretsmanager', 'get-secret-value',
             '--secret-id', config['aws']['secrets_manager']['github_pat_secret_name'],
             '--region', config['aws']['region'],
             '--query', 'SecretString',
             '--output', 'text'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        secret_data = json.loads(result.stdout)
        return secret_data['github_token']

    def test_oidc_token_exists(self, oidc_token):
        assert oidc_token is not None

    def test_oidc_token_not_empty(self, oidc_token):
        assert len(oidc_token) > 0

    def test_aws_access_key_id_exists(self, aws_creds):
        assert aws_creds['access_key_id'] is not None

    def test_aws_secret_access_key_exists(self, aws_creds):
        assert aws_creds['secret_access_key'] is not None

    def test_aws_session_token_exists(self, aws_creds):
        assert aws_creds['session_token'] is not None

    def test_github_pat_exists(self, github_pat):
        assert github_pat is not None

    def test_github_pat_has_correct_prefix(self, github_pat):
        assert github_pat.startswith('ghp_')

    def test_assumed_role_arn_contains_role_name(self, config, aws_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = aws_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = aws_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = aws_creds['session_token']

        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity',
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        identity = json.loads(result.stdout)
        assert config['aws']['iam_role_name'] in identity['Arn']

    def test_assumed_role_arn_is_assumed_role_type(self, config, aws_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = aws_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = aws_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = aws_creds['session_token']

        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity',
             '--region', config['aws']['region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )

        identity = json.loads(result.stdout)
        assert 'assumed-role' in identity['Arn']

    def test_github_runner_token_response_has_token_field(self, config, github_pat):
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST',
             '-H', 'Accept: application/vnd.github+json',
             '-H', f'Authorization: Bearer {github_pat}',
             '-H', 'X-GitHub-Api-Version: 2022-11-28',
             f"https://api.github.com/repos/{config['github']['org']}/{config['github']['repo']}/actions/runners/registration-token"],
            capture_output=True,
            text=True,
            check=True
        )

        response = json.loads(result.stdout)
        assert 'token' in response

    def test_github_runner_token_exists(self, config, github_pat):
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST',
             '-H', 'Accept: application/vnd.github+json',
             '-H', f'Authorization: Bearer {github_pat}',
             '-H', 'X-GitHub-Api-Version: 2022-11-28',
             f"https://api.github.com/repos/{config['github']['org']}/{config['github']['repo']}/actions/runners/registration-token"],
            capture_output=True,
            text=True,
            check=True
        )

        response = json.loads(result.stdout)
        assert response['token'] is not None

    def test_github_runner_token_not_empty(self, config, github_pat):
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST',
             '-H', 'Accept: application/vnd.github+json',
             '-H', f'Authorization: Bearer {github_pat}',
             '-H', 'X-GitHub-Api-Version: 2022-11-28',
             f"https://api.github.com/repos/{config['github']['org']}/{config['github']['repo']}/actions/runners/registration-token"],
            capture_output=True,
            text=True,
            check=True
        )

        response = json.loads(result.stdout)
        assert len(response['token']) > 0

    def test_github_runner_token_has_expiration(self, config, github_pat):
        result = subprocess.run(
            ['curl', '-s', '-X', 'POST',
             '-H', 'Accept: application/vnd.github+json',
             '-H', f'Authorization: Bearer {github_pat}',
             '-H', 'X-GitHub-Api-Version: 2022-11-28',
             f"https://api.github.com/repos/{config['github']['org']}/{config['github']['repo']}/actions/runners/registration-token"],
            capture_output=True,
            text=True,
            check=True
        )

        response = json.loads(result.stdout)
        assert 'expires_at' in response
