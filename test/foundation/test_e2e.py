import json
import os
import subprocess
import dns.resolver
import pytest


def get_github_oidc_token():
    token_url = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_URL')
    token_request_token = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_TOKEN')
    if not token_url or not token_request_token:
        pytest.skip("OIDC token not available")
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
        pytest.fail("Could not retrieve OIDC token")
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
    def oidc_token(self):
        return get_github_oidc_token()

    @pytest.fixture
    def aws_creds(self, config, oidc_token):
        return assume_role_with_oidc(
            config['aws_account_id'],
            config['aws_region'],
            config['github_actions_role_name'],
            oidc_token
        )

    def test_complete_oidc_workflow(self, config, oidc_token, aws_creds):
        assert oidc_token is not None
        assert len(oidc_token) > 0
        assert aws_creds['access_key_id'] is not None
        assert aws_creds['secret_access_key'] is not None
        assert aws_creds['session_token'] is not None

    def test_assumed_role_has_correct_identity(self, config, aws_creds):
        env = os.environ.copy()
        env['AWS_ACCESS_KEY_ID'] = aws_creds['access_key_id']
        env['AWS_SECRET_ACCESS_KEY'] = aws_creds['secret_access_key']
        env['AWS_SESSION_TOKEN'] = aws_creds['session_token']
        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity',
             '--region', config['aws_region'],
             '--output', 'json'],
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        identity = json.loads(result.stdout)
        assert config['github_actions_role_name'] in identity['Arn']
        assert 'assumed-role' in identity['Arn']


def test_can_create_and_resolve_record_via_route53_nameserver(route53_client, hosted_zone, config):
    import time
    domain_name = config['domain_name']
    ns_response = route53_client.get_hosted_zone(Id=hosted_zone['Id'])
    name_servers = ns_response['DelegationSet']['NameServers']
    test_record_name = f"e2e-test.{domain_name}"
    test_value = "e2e-test-value-12345"
    try:
        change_response = route53_client.change_resource_record_sets(
            HostedZoneId=hosted_zone['Id'],
            ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': test_record_name,
                        'Type': 'TXT',
                        'TTL': 60,
                        'ResourceRecords': [{'Value': f'"{test_value}"'}]
                    }
                }]
            }
        )
        change_id = change_response['ChangeInfo']['Id']
        for _ in range(30):
            change_status = route53_client.get_change(Id=change_id)
            if change_status['ChangeInfo']['Status'] == 'INSYNC':
                break
            time.sleep(1)
        ns_ip = dns.resolver.resolve(name_servers[0], 'A')[0].to_text()
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [ns_ip]
        answers = resolver.resolve(test_record_name, 'TXT')
        resolved_value = str(answers[0]).strip('"')
        assert resolved_value == test_value
    finally:
        try:
            route53_client.change_resource_record_sets(
                HostedZoneId=hosted_zone['Id'],
                ChangeBatch={
                    'Changes': [{
                        'Action': 'DELETE',
                        'ResourceRecordSet': {
                            'Name': test_record_name,
                            'Type': 'TXT',
                            'TTL': 60,
                            'ResourceRecords': [{'Value': f'"{test_value}"'}]
                        }
                    }]
                }
            )
        except:
            pass
