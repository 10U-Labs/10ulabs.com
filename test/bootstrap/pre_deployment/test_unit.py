#!/usr/bin/env python3
"""
Unit tests for bootstrap.py using pytest.

Uses only unittest.mock from standard library - no external test dependencies.
Pytest itself comes with Python or can be installed via system package manager.
"""

import json
import subprocess
import sys
import urllib.error
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add src/bootstrap to path
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / 'src' / 'bootstrap'))

import bootstrap


class TestHelperFunctions:
    """Test helper functions."""

    @patch('os.environ.get', return_value='true')
    def test_is_running_in_github_actions_returns_true(self, mock_env):
        """Test is_running_in_github_actions returns True when GITHUB_ACTIONS=true."""
        result = bootstrap.is_running_in_github_actions()
        assert result is True
        mock_env.assert_called_once_with('GITHUB_ACTIONS', '')

    @patch('os.environ.get', return_value='false')
    def test_is_running_in_github_actions_returns_false(self, mock_env):
        """Test is_running_in_github_actions returns False when GITHUB_ACTIONS=false."""
        result = bootstrap.is_running_in_github_actions()
        assert result is False

    @patch('os.environ.get', return_value='')
    def test_is_running_in_github_actions_returns_false_when_empty(self, mock_env):
        """Test is_running_in_github_actions returns False when GITHUB_ACTIONS is empty."""
        result = bootstrap.is_running_in_github_actions()
        assert result is False

    @patch('bootstrap.assume_role_with_oidc')
    @patch('bootstrap.get_oidc_token')
    def test_detect_bootstrap_state_warm_with_oidc(self, mock_get_token, mock_assume_role):
        """Test detect_bootstrap_state returns warm when OIDC role assumption succeeds."""
        mock_get_token.return_value = 'test-oidc-token'
        mock_assume_role.return_value = {
            'access_key_id': 'AKIATEST',
            'secret_access_key': 'test',
            'session_token': 'token'
        }

        result = bootstrap.detect_bootstrap_state('123456789012', 'us-east-1', 'test-role')

        assert result == 'warm'
        mock_assume_role.assert_called_once_with('123456789012', 'us-east-1', 'test-role')

    @patch('bootstrap.assume_role_with_oidc')
    @patch('bootstrap.get_oidc_token')
    def test_detect_bootstrap_state_cold_with_oidc_failure(self, mock_get_token, mock_assume_role):
        """Test detect_bootstrap_state returns cold when OIDC role assumption fails."""
        mock_get_token.return_value = 'test-oidc-token'
        mock_assume_role.return_value = None

        result = bootstrap.detect_bootstrap_state('123456789012', 'us-east-1', 'test-role')

        assert result == 'cold'

    @patch('urllib.request.urlopen')
    @patch('bootstrap.get_oidc_token')
    def test_detect_bootstrap_state_warm_with_credentials(self, mock_get_token, mock_urlopen):
        """Test detect_bootstrap_state returns warm when OIDC provider exists."""
        mock_get_token.return_value = None
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = bootstrap.detect_bootstrap_state(
            '123456789012', 'us-east-1', 'test-role',
            'AKIATEST', 'secret'
        )

        assert result == 'warm'

    @patch('urllib.request.urlopen')
    @patch('bootstrap.get_oidc_token')
    def test_detect_bootstrap_state_cold_with_credentials(self, mock_get_token, mock_urlopen):
        """Test detect_bootstrap_state returns cold when OIDC provider doesn't exist."""
        from urllib.error import HTTPError
        from io import BytesIO
        mock_get_token.return_value = None
        error = HTTPError('url', 404, 'Not Found', {}, BytesIO(b'Not Found'))
        mock_urlopen.side_effect = error

        result = bootstrap.detect_bootstrap_state(
            '123456789012', 'us-east-1', 'test-role',
            'AKIATEST', 'secret'
        )

        assert result == 'cold'

    @patch('bootstrap.get_oidc_token')
    def test_detect_bootstrap_state_cold_with_no_credentials(self, mock_get_token):
        """Test detect_bootstrap_state returns cold when no credentials available."""
        mock_get_token.return_value = None

        result = bootstrap.detect_bootstrap_state('123456789012', 'us-east-1', 'test-role')

        assert result == 'cold'

    @patch('bootstrap.STSClient')
    @patch('bootstrap.get_oidc_token')
    def test_assume_role_with_oidc_success(self, mock_get_token, mock_sts_class):
        """Test assume_role_with_oidc returns credentials on success."""
        mock_get_token.return_value = 'test-oidc-token'
        mock_sts_instance = MagicMock()
        mock_sts_instance.assume_role_with_web_identity.return_value = {
            'access_key_id': 'AKIATEST',
            'secret_access_key': 'test',
            'session_token': 'token'
        }
        mock_sts_class.return_value = mock_sts_instance

        result = bootstrap.assume_role_with_oidc('123456789012', 'us-east-1', 'test-role')

        assert result is not None
        assert result['access_key_id'] == 'AKIATEST'

    @patch('bootstrap.get_oidc_token')
    def test_assume_role_with_oidc_no_token(self, mock_get_token):
        """Test assume_role_with_oidc returns None when no OIDC token."""
        mock_get_token.return_value = None

        result = bootstrap.assume_role_with_oidc('123456789012', 'us-east-1', 'test-role')

        assert result is None

    @patch('bootstrap.STSClient')
    @patch('bootstrap.get_oidc_token')
    def test_assume_role_with_oidc_failure(self, mock_get_token, mock_sts_class):
        """Test assume_role_with_oidc returns None when role assumption fails."""
        mock_get_token.return_value = 'test-oidc-token'
        mock_sts_instance = MagicMock()
        mock_sts_instance.assume_role_with_web_identity.return_value = None
        mock_sts_class.return_value = mock_sts_instance

        result = bootstrap.assume_role_with_oidc('123456789012', 'us-east-1', 'test-role')

        assert result is None

    @patch('bootstrap.SecretsManagerClient')
    def test_get_secret_from_secrets_manager_success(self, mock_sm_class):
        """Test get_secret_from_secrets_manager returns secret value."""
        mock_sm_instance = MagicMock()
        mock_sm_instance.get_secret_value.return_value = {'key': 'value'}
        mock_sm_class.return_value = mock_sm_instance

        result = bootstrap.get_secret_from_secrets_manager(
            'test-secret', 'us-east-1', 'AKIATEST', 'secret'
        )

        assert result == {'key': 'value'}
        mock_sm_instance.get_secret_value.assert_called_once_with('test-secret')


class TestAWSClientStdlib:
    """Test AWSClientStdlib methods."""

    @pytest.fixture
    def client(self):
        """Create AWSClientStdlib fixture."""
        return bootstrap.AWSClientStdlib('us-east-1', 'AKIATEST', 'secret123')

    def test_init_sets_credentials(self, client):
        """Test __init__ sets credentials correctly."""
        assert client.region == 'us-east-1'
        assert client.sts is not None
        assert client.iam is not None
        assert client.secrets is not None
        assert isinstance(client.sts, bootstrap.STSClient)
        assert isinstance(client.iam, bootstrap.IAMClient)
        assert isinstance(client.secrets, bootstrap.SecretsManagerClient)

    @patch('urllib.request.urlopen')
    def test_oidc_provider_exists_returns_true_when_found(self, mock_urlopen, client):
        """Test oidc_provider_exists returns True when provider exists."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.oidc_provider_exists('123456789012')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_oidc_provider_exists_returns_false_on_404(self, mock_urlopen, client):
        """Test oidc_provider_exists returns False on 404."""
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 404, 'Not Found', {}, BytesIO(b'Not Found'))
        mock_urlopen.side_effect = error

        result = client.iam.oidc_provider_exists('123456789012')

        assert result is False

    @patch('urllib.request.urlopen')
    def test_create_oidc_provider_returns_true_on_success(self, mock_urlopen, client):
        """Test create_oidc_provider returns True on success."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.create_oidc_provider()

        assert result is True
        mock_urlopen.assert_called_once()

    @patch('urllib.request.urlopen')
    def test_role_exists_returns_true_when_found(self, mock_urlopen, client):
        """Test role_exists returns True when role exists."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.role_exists('test-role')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_role_exists_returns_false_on_404(self, mock_urlopen, client):
        """Test role_exists returns False on 404."""
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 404, 'Not Found', {}, BytesIO(b'Not Found'))
        mock_urlopen.side_effect = error

        result = client.iam.role_exists('test-role')

        assert result is False

    @patch('urllib.request.urlopen')
    def test_create_role_returns_true_on_success(self, mock_urlopen, client):
        """Test create_role returns True on success."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        trust_policy = {"Version": "2012-10-17", "Statement": []}
        result = client.iam.create_role('test-role', trust_policy)

        assert result is True

    @patch('urllib.request.urlopen')
    def test_attach_managed_policy_returns_true_on_success(self, mock_urlopen, client):
        """Test attach_managed_policy returns True on success."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.attach_managed_policy('test-role', 'arn:aws:iam::aws:policy/PowerUserAccess')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_put_role_policy_returns_true_on_success(self, mock_urlopen, client):
        """Test put_role_policy returns True on success."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        policy_doc = {"Version": "2012-10-17", "Statement": []}
        result = client.iam.put_role_policy('test-role', 'TestPolicy', policy_doc)

        assert result is True

    @patch('urllib.request.urlopen')
    def test_managed_policy_attached_returns_true_when_attached(self, mock_urlopen, client):
        """Test managed_policy_attached returns True when policy is attached."""
        xml_response = '''<?xml version="1.0"?>
        <ListAttachedRolePoliciesResponse>
            <ListAttachedRolePoliciesResult>
                <AttachedPolicies>
                    <member>
                        <PolicyArn>arn:aws:iam::aws:policy/PowerUserAccess</PolicyArn>
                    </member>
                </AttachedPolicies>
            </ListAttachedRolePoliciesResult>
        </ListAttachedRolePoliciesResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.managed_policy_attached('test-role', 'arn:aws:iam::aws:policy/PowerUserAccess')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_managed_policy_attached_returns_false_when_not_attached(self, mock_urlopen, client):
        """Test managed_policy_attached returns False when policy not attached."""
        xml_response = '''<?xml version="1.0"?>
        <ListAttachedRolePoliciesResponse>
            <ListAttachedRolePoliciesResult>
                <AttachedPolicies></AttachedPolicies>
            </ListAttachedRolePoliciesResult>
        </ListAttachedRolePoliciesResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.managed_policy_attached('test-role', 'arn:aws:iam::aws:policy/PowerUserAccess')

        assert result is False

    @patch('urllib.request.urlopen')
    def test_inline_policy_exists_returns_true_when_found(self, mock_urlopen, client):
        """Test inline_policy_exists returns True when policy exists."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.inline_policy_exists('test-role', 'TestPolicy')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_inline_policy_exists_returns_false_on_404(self, mock_urlopen, client):
        """Test inline_policy_exists returns False on 404."""
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 404, 'Not Found', {}, BytesIO(b'Not Found'))
        mock_urlopen.side_effect = error

        result = client.iam.inline_policy_exists('test-role', 'TestPolicy')

        assert result is False

    @patch('urllib.request.urlopen')
    def test_create_secret_returns_true_on_success(self, mock_urlopen, client):
        """Test create_secret returns True on success."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.secrets.create_secret('test-secret', {'key': 'value'})

        assert result is True

    @patch('urllib.request.urlopen')
    def test_update_secret_returns_true_on_success(self, mock_urlopen, client):
        """Test update_secret returns True on success."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test", "VersionId": "v1"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.secrets.update_secret('test-secret', {'key': 'new_value'})

        assert result is True

    @patch('urllib.request.urlopen')
    def test_secret_exists_returns_true_when_found(self, mock_urlopen, client):
        """Test secret_exists returns True when secret exists."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.secrets.secret_exists('test-secret')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_secret_exists_returns_false_on_400(self, mock_urlopen, client):
        """Test secret_exists returns False on 400 (ResourceNotFoundException)."""
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 400, 'Bad Request', {}, BytesIO(b'ResourceNotFoundException'))
        mock_urlopen.side_effect = error

        result = client.secrets.secret_exists('test-secret')

        assert result is False

    @patch('urllib.request.urlopen')
    def test_get_secret_value_returns_secret_on_success(self, mock_urlopen, client):
        """Test get_secret_value returns secret value on success."""
        secret_data = {'github_token': 'ghp_test123', 'github_org': 'test-org'}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            'SecretString': json.dumps(secret_data)
        }).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.secrets.get_secret_value('test-secret')

        assert result == secret_data

    @patch('urllib.request.urlopen')
    def test_get_secret_value_returns_none_on_not_found(self, mock_urlopen, client):
        """Test get_secret_value returns None when secret not found."""
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 400, 'Bad Request', {}, BytesIO(b'ResourceNotFoundException'))
        mock_urlopen.side_effect = error

        result = client.secrets.get_secret_value('nonexistent-secret')

        assert result is None

    @patch('urllib.request.urlopen')
    def test_get_secret_value_returns_none_on_missing_secret_string(self, mock_urlopen, client):
        """Test get_secret_value returns None when SecretString is missing."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.secrets.get_secret_value('test-secret')

        assert result is None

    @patch('urllib.request.urlopen')
    def test_delete_secret_returns_true_on_success(self, mock_urlopen, client):
        """Test delete_secret returns True on success."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"ARN": "arn:aws:secretsmanager:us-east-1:123456789012:secret:test"}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.secrets.delete_secret('test-secret')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_detach_managed_policy_returns_true_on_success(self, mock_urlopen, client):
        """Test detach_managed_policy returns True on success."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.detach_managed_policy('test-role', 'arn:aws:iam::aws:policy/PowerUserAccess')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_delete_role_policy_returns_true_on_success(self, mock_urlopen, client):
        """Test delete_role_policy returns True on success."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.delete_role_policy('test-role', 'TestPolicy')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_delete_role_returns_true_on_success(self, mock_urlopen, client):
        """Test delete_role returns True on success."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.delete_role('test-role')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_delete_oidc_provider_returns_true_on_success(self, mock_urlopen, client):
        """Test delete_oidc_provider returns True on success."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.delete_oidc_provider('123456789012')

        assert result is True

    @patch('urllib.request.urlopen')
    def test_get_role_trust_policy_returns_policy_on_success(self, mock_urlopen, client):
        """Test get_role_trust_policy returns trust policy when role exists."""
        import urllib.parse
        trust_policy = {"Version": "2012-10-17", "Statement": []}
        encoded_policy = urllib.parse.quote(json.dumps(trust_policy))
        xml_response = f'''<?xml version="1.0"?>
        <GetRoleResponse>
            <GetRoleResult>
                <Role>
                    <AssumeRolePolicyDocument>{encoded_policy}</AssumeRolePolicyDocument>
                </Role>
            </GetRoleResult>
        </GetRoleResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.iam.get_role_trust_policy('test-role')

        assert result == trust_policy

    @patch('urllib.request.urlopen')
    def test_get_role_trust_policy_returns_none_on_error(self, mock_urlopen, client):
        """Test get_role_trust_policy returns None on error."""
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 404, 'Not Found', {}, BytesIO(b'Not Found'))
        mock_urlopen.side_effect = error

        result = client.iam.get_role_trust_policy('test-role')

        assert result is None

    @patch('urllib.request.urlopen')
    def test_update_role_trust_policy_returns_true_on_success(self, mock_urlopen, client):
        """Test update_role_trust_policy returns True on success."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        trust_policy = {"Version": "2012-10-17", "Statement": []}
        result = client.iam.update_role_trust_policy('test-role', trust_policy)

        assert result is True

    @patch('urllib.request.urlopen')
    def test_update_role_trust_policy_returns_false_on_error(self, mock_urlopen, client):
        """Test update_role_trust_policy returns False on error."""
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 400, 'Bad Request', {}, BytesIO(b'Error'))
        mock_urlopen.side_effect = error

        trust_policy = {"Version": "2012-10-17", "Statement": []}
        result = client.iam.update_role_trust_policy('test-role', trust_policy)

        assert result is False

    @patch('urllib.request.urlopen')
    def test_get_account_id_returns_account_id(self, mock_urlopen, client):
        """Test get_account_id returns AWS account ID from STS."""
        xml_response = '''<?xml version="1.0"?>
        <GetCallerIdentityResponse>
            <GetCallerIdentityResult>
                <Account>123456789012</Account>
            </GetCallerIdentityResult>
        </GetCallerIdentityResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.sts.get_account_id()

        assert result == '123456789012'

    @patch('urllib.request.urlopen')
    def test_sts_client_test_sts_access_succeeds(self, mock_urlopen, client):
        """Test STSClient.test_sts_access succeeds on valid credentials."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Should not raise
        client.sts.test_sts_access()

        mock_urlopen.assert_called_once()

    @patch('urllib.request.urlopen')
    def test_assume_role_with_web_identity_returns_credentials_on_success(self, mock_urlopen, client):
        """Test assume_role_with_web_identity returns temporary credentials on success."""
        xml_response = '''<?xml version="1.0"?>
        <AssumeRoleWithWebIdentityResponse>
            <AssumeRoleWithWebIdentityResult>
                <Credentials>
                    <AccessKeyId>AKIAIOSFODNN7EXAMPLE</AccessKeyId>
                    <SecretAccessKey>wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY</SecretAccessKey>
                    <SessionToken>FQoGZXIvYXdzEBYaD...</SessionToken>
                </Credentials>
            </AssumeRoleWithWebIdentityResult>
        </AssumeRoleWithWebIdentityResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.sts.assume_role_with_web_identity(
            'arn:aws:iam::123456789012:role/test-role',
            'test-web-identity-token'
        )

        assert result is not None
        assert result['access_key_id'] == 'AKIAIOSFODNN7EXAMPLE'
        assert result['secret_access_key'] == 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'
        assert result['session_token'] == 'FQoGZXIvYXdzEBYaD...'

    @patch('urllib.request.urlopen')
    def test_assume_role_with_web_identity_returns_none_on_http_error(self, mock_urlopen, client):
        """Test assume_role_with_web_identity returns None on HTTP error."""
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 403, 'Forbidden', {}, BytesIO(b'Access Denied'))
        mock_urlopen.side_effect = error

        result = client.sts.assume_role_with_web_identity(
            'arn:aws:iam::123456789012:role/test-role',
            'invalid-token'
        )

        assert result is None

    @patch('urllib.request.urlopen')
    def test_assume_role_with_web_identity_returns_none_on_parse_error(self, mock_urlopen, client):
        """Test assume_role_with_web_identity returns None on XML parse error."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'Invalid XML'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.sts.assume_role_with_web_identity(
            'arn:aws:iam::123456789012:role/test-role',
            'test-token'
        )

        assert result is None

    @patch('urllib.request.urlopen')
    def test_assume_role_with_web_identity_returns_none_on_missing_credentials(self, mock_urlopen, client):
        """Test assume_role_with_web_identity returns None when credentials missing from response."""
        xml_response = '''<?xml version="1.0"?>
        <AssumeRoleWithWebIdentityResponse>
            <AssumeRoleWithWebIdentityResult>
            </AssumeRoleWithWebIdentityResult>
        </AssumeRoleWithWebIdentityResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.sts.assume_role_with_web_identity(
            'arn:aws:iam::123456789012:role/test-role',
            'test-token'
        )

        assert result is None

    @patch('urllib.request.urlopen')
    def test_iam_client_test_iam_access_succeeds(self, mock_urlopen, client):
        """Test IAMClient.test_iam_access succeeds when IAM accessible."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Should not raise
        client.iam.test_iam_access()

        mock_urlopen.assert_called_once()

    @patch('urllib.request.urlopen')
    def test_secrets_manager_client_test_access_succeeds(self, mock_urlopen, client):
        """Test SecretsManagerClient.test_secrets_manager_access succeeds."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'{"SecretList": []}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Should not raise
        client.secrets.test_secrets_manager_access()

        mock_urlopen.assert_called_once()

    @patch('urllib.request.urlopen')
    def test_stdlib_get_account_id_delegates_to_iam(self, mock_urlopen, client):
        """Test AWSClientStdlib.get_account_id delegates to IAM client."""
        xml_response = '''<?xml version="1.0"?>
        <GetCallerIdentityResponse>
            <GetCallerIdentityResult>
                <Account>987654321098</Account>
            </GetCallerIdentityResult>
        </GetCallerIdentityResponse>'''

        mock_response = MagicMock()
        mock_response.read.return_value = xml_response.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = client.get_account_id()

        assert result == '987654321098'

    @patch('urllib.request.urlopen')
    def test_validate_access_succeeds_when_all_services_accessible(self, mock_urlopen, client):
        """Test validate_access succeeds when STS, IAM, and Secrets Manager all accessible."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'<Response></Response>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Should not raise
        client.validate_access()

        # Should have called all 3 services (STS, IAM, Secrets Manager)
        assert mock_urlopen.call_count == 3

    @patch('urllib.request.urlopen')
    def test_validate_access_raises_on_sts_failure(self, mock_urlopen, client):
        """Test validate_access raises HTTPError with clear message on STS failure."""
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 403, 'Forbidden', {}, BytesIO(b'Forbidden'))
        mock_urlopen.side_effect = error

        with pytest.raises(bootstrap.AWSHTTPError):
            client.validate_access()

    @patch('urllib.request.urlopen')
    def test_validate_access_raises_on_iam_failure(self, mock_urlopen, client):
        """Test validate_access raises HTTPError with clear message on IAM failure."""
        from urllib.error import HTTPError
        from io import BytesIO

        # STS succeeds, IAM fails
        def side_effect(*args, **kwargs):
            if mock_urlopen.call_count == 1:
                mock_response = MagicMock()
                mock_response.read.return_value = b'<Response></Response>'
                return mock_response.__enter__.return_value
            else:
                raise HTTPError('url', 403, 'Forbidden', {}, BytesIO(b'Forbidden'))

        mock_urlopen.side_effect = side_effect

        with pytest.raises(bootstrap.AWSHTTPError):
            client.validate_access()

    @patch('urllib.request.urlopen')
    def test_validate_access_raises_on_secrets_manager_failure(self, mock_urlopen, client):
        """Test validate_access raises HTTPError with clear message on Secrets Manager failure."""
        from urllib.error import HTTPError
        from io import BytesIO

        # STS and IAM succeed, Secrets Manager fails
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                mock_response = MagicMock()
                mock_response.read.return_value = b'<Response></Response>'
                mock_response.__enter__ = MagicMock(return_value=mock_response)
                mock_response.__exit__ = MagicMock(return_value=False)
                return mock_response
            else:
                raise HTTPError('url', 403, 'Forbidden', {}, BytesIO(b'Forbidden'))

        mock_urlopen.side_effect = side_effect

        with pytest.raises(bootstrap.AWSHTTPError):
            client.validate_access()


class TestPolicyGenerators:
    """Test policy document generation functions."""

    def test_create_trust_policy_generates_valid_policy(self):
        """Test create_trust_policy generates correct structure."""
        policy = bootstrap.create_trust_policy('123456789012', 'test-org', 'test-repo')

        assert policy['Version'] == '2012-10-17'
        assert len(policy['Statement']) == 1

        statement = policy['Statement'][0]
        assert statement['Effect'] == 'Allow'
        assert statement['Action'] == 'sts:AssumeRoleWithWebIdentity'
        assert 'Federated' in statement['Principal']
        assert '123456789012' in statement['Principal']['Federated']
        assert 'test-org/test-repo' in statement['Condition']['StringLike']['token.actions.githubusercontent.com:sub']

    def test_create_iam_role_management_policy_includes_required_actions(self):
        """Test IAM role management policy includes all required actions."""
        policy = bootstrap.create_iam_role_management_policy()

        assert policy['Version'] == '2012-10-17'
        assert len(policy['Statement']) == 3  # IAM, Bedrock control plane, Bedrock InvokeModel

        # Check IAM statement (statement 0)
        iam_statement = policy['Statement'][0]
        assert iam_statement['Effect'] == 'Allow'
        assert 'iam:CreateRole' in iam_statement['Action']
        assert 'iam:DeleteRole' in iam_statement['Action']
        assert 'iam:AttachRolePolicy' in iam_statement['Action']
        assert 'iam:PassRole' in iam_statement['Action']
        assert iam_statement['Resource'] == '*'

    def test_normalize_policy_produces_canonical_json(self):
        """Test normalize_policy produces canonical JSON string."""
        policy = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }

        result = bootstrap.normalize_policy(policy)

        # Should be compact JSON with sorted keys
        assert '"Action":"s3:GetObject"' in result
        assert '"Effect":"Allow"' in result
        assert '"Version":"2012-10-17"' in result
        # No spaces after separators
        assert ', ' not in result
        assert ': ' not in result

    def test_policies_equal_returns_true_for_identical_policies(self):
        """Test policies_equal returns True for identical policies."""
        policy1 = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }
        policy2 = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }

        assert bootstrap.policies_equal(policy1, policy2) is True

    def test_policies_equal_returns_true_for_reordered_keys(self):
        """Test policies_equal returns True for policies with reordered keys."""
        policy1 = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }
        policy2 = {
            "Statement": [{"Action": "s3:GetObject", "Effect": "Allow"}],
            "Version": "2012-10-17"
        }

        assert bootstrap.policies_equal(policy1, policy2) is True

    def test_policies_equal_returns_false_for_different_policies(self):
        """Test policies_equal returns False for different policies."""
        policy1 = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}]
        }
        policy2 = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "Allow", "Action": "s3:PutObject"}]
        }

        assert bootstrap.policies_equal(policy1, policy2) is False

    def test_trust_policy_requires_specific_github_org_repo(self):
        """Test trust policy restricts access to specific GitHub org/repo only."""
        policy = bootstrap.create_trust_policy('123456789012', 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        # Verify condition restricts to specific org/repo
        sub_condition = statement['Condition']['StringLike']['token.actions.githubusercontent.com:sub']
        assert sub_condition == 'repo:test-org/test-repo:*'
        # Verify it's not overly permissive (e.g., not 'repo:*:*' or 'repo:test-org/*')
        assert ':*:*' not in sub_condition
        assert sub_condition.startswith('repo:test-org/test-repo:')

    def test_trust_policy_requires_correct_audience(self):
        """Test trust policy requires sts.amazonaws.com audience."""
        policy = bootstrap.create_trust_policy('123456789012', 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        # Verify audience condition exists and is correct
        assert 'StringEquals' in statement['Condition']
        aud_condition = statement['Condition']['StringEquals']['token.actions.githubusercontent.com:aud']
        assert aud_condition == 'sts.amazonaws.com'

    def test_trust_policy_uses_correct_oidc_provider_arn(self):
        """Test trust policy uses correct OIDC provider ARN format."""
        account_id = '123456789012'
        policy = bootstrap.create_trust_policy(account_id, 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        federated_principal = statement['Principal']['Federated']

        # Verify correct ARN format
        expected_arn = f'arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com'
        assert federated_principal == expected_arn

    def test_trust_policy_only_allows_assume_role_with_web_identity(self):
        """Test trust policy only allows AssumeRoleWithWebIdentity action."""
        policy = bootstrap.create_trust_policy('123456789012', 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        # Verify only one specific action is allowed
        assert statement['Action'] == 'sts:AssumeRoleWithWebIdentity'
        # Verify it's not a list of actions
        assert isinstance(statement['Action'], str)

    def test_trust_policy_no_wildcard_principals(self):
        """Test trust policy does not allow wildcard principals."""
        policy = bootstrap.create_trust_policy('123456789012', 'test-org', 'test-repo')

        statement = policy['Statement'][0]
        # Verify principal is not wildcard
        assert statement['Principal'] != '*'
        assert 'AWS' not in statement['Principal'] or statement['Principal'].get('AWS') != '*'

    def test_trust_policy_conditions_are_restrictive(self):
        """Test trust policy conditions are properly restrictive."""
        policy = bootstrap.create_trust_policy('123456789012', 'my-org', 'my-repo')

        statement = policy['Statement'][0]
        conditions = statement['Condition']

        # Verify both StringLike and StringEquals conditions exist
        assert 'StringLike' in conditions
        assert 'StringEquals' in conditions

        # Verify sub claim is scoped to specific repo
        sub = conditions['StringLike']['token.actions.githubusercontent.com:sub']
        assert sub == 'repo:my-org/my-repo:*'

        # Verify audience is exact match
        aud = conditions['StringEquals']['token.actions.githubusercontent.com:aud']
        assert aud == 'sts.amazonaws.com'


class TestSecretValueGeneration:
    """Test secret value generation for GitHub PAT."""

    def test_create_secret_value_generates_correct_structure(self):
        """Test create_secret_value generates correct structure."""
        result = bootstrap.create_secret_value('ghp_test123', 'test-org', 'test-repo')

        assert result['auth_method'] == 'classic-pat'
        assert result['github_token'] == 'ghp_test123'
        assert result['github_org'] == 'test-org'
        assert result['github_repo'] == 'test-repo'
        assert result['created_by'] == 'bootstrap-script'
        assert 'created_at' in result


class TestCreateResources:
    """Test create_resources function."""

    @pytest.fixture
    def args(self):
        """Create mock args fixture."""
        args = Mock()
        args.aws_account_id = '123456789012'
        args.aws_region = 'us-east-1'
        args.aws_iam_role_name = 'TestRole'
        args.github_org = 'test-org'
        args.github_repo = 'test-repo'
        args.aws_access_key_id = 'AKIATEST'
        args.aws_secret_access_key = 'secret123'
        args.github_token = 'ghp_test123'
        return args

    @patch('bootstrap.validate_oidc_role_permissions')
    @patch('bootstrap.validate_github_pat')
    @patch('bootstrap.validate_aws_credentials')
    @patch('bootstrap.is_running_in_github_actions', return_value=False)
    @patch('bootstrap.AWSClientStdlib')
    def test_create_uses_stdlib_client_in_local_mode(self, mock_stdlib, mock_gh_check,
                                                      mock_aws_val, mock_pat_val, mock_role_val, args):
        """Test that create_resources uses AWSClientStdlib in local mode."""
        # Setup mock client
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_client.iam.oidc_provider_exists.return_value = False
        mock_client.iam.create_oidc_provider.return_value = True
        mock_client.iam.role_exists.return_value = False
        mock_client.iam.create_role.return_value = True
        mock_client.iam.managed_policy_attached.return_value = False
        mock_client.iam.attach_managed_policy.return_value = True
        mock_client.iam.inline_policy_exists.return_value = False
        mock_client.iam.put_role_policy.return_value = True
        mock_client.secrets.create_secret.return_value = True

        result = bootstrap.create_resources(args)

        assert result == 0
        mock_stdlib.assert_called_once_with('us-east-1', access_key_id='AKIATEST', secret_access_key='secret123', session_token=None, bedrock_model_id=args.bedrock_model_id)
        # Verify validation functions were called
        mock_aws_val.assert_called_once()
        mock_pat_val.assert_called_once()
        mock_role_val.assert_called_once()

    @patch('bootstrap.validate_oidc_role_permissions')
    @patch('bootstrap.validate_github_pat')
    @patch('bootstrap.validate_aws_credentials')
    @patch('bootstrap.is_running_in_github_actions', return_value=True)
    @patch('bootstrap.AWSClientStdlib')
    def test_create_skips_existing_oidc_provider(self, mock_stdlib, mock_gh_check,
                                                  mock_aws_val, mock_pat_val, mock_role_val, args):
        """Test that create_resources skips OIDC provider if it already exists."""
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_client.iam.oidc_provider_exists.return_value = True  # Already exists
        mock_client.iam.role_exists.return_value = False
        mock_client.iam.create_role.return_value = True
        mock_client.iam.managed_policy_attached.return_value = False
        mock_client.iam.attach_managed_policy.return_value = True
        mock_client.iam.inline_policy_exists.return_value = False
        mock_client.iam.put_role_policy.return_value = True
        mock_client.secrets.create_secret.return_value = True

        result = bootstrap.create_resources(args)

        assert result == 0
        mock_client.iam.create_oidc_provider.assert_not_called()

    @patch('bootstrap.validate_oidc_role_permissions')
    @patch('bootstrap.validate_github_pat')
    @patch('bootstrap.validate_aws_credentials')
    @patch('bootstrap.is_running_in_github_actions', return_value=False)
    @patch('bootstrap.AWSClientStdlib')
    def test_create_returns_error_when_oidc_creation_fails(self, mock_stdlib, mock_gh_check,
                                                            mock_aws_val, mock_pat_val, mock_role_val, args):
        """Test that create_resources returns error code when OIDC creation fails."""
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_client.iam.oidc_provider_exists.return_value = False
        mock_client.iam.create_oidc_provider.return_value = False  # Fails

        result = bootstrap.create_resources(args)

        assert result == 1

    @patch('bootstrap.validate_oidc_role_permissions')
    @patch('bootstrap.validate_github_pat')
    @patch('bootstrap.validate_aws_credentials')
    @patch('bootstrap.is_running_in_github_actions', return_value=False)
    @patch('bootstrap.AWSClientStdlib')
    def test_create_returns_error_when_role_creation_fails(self, mock_stdlib, mock_gh_check,
                                                            mock_aws_val, mock_pat_val, mock_role_val, args):
        """Test that create_resources returns error code when role creation fails."""
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_client.iam.oidc_provider_exists.return_value = True
        mock_client.iam.role_exists.return_value = False
        mock_client.iam.create_role.return_value = False  # Fails

        result = bootstrap.create_resources(args)

        assert result == 1


class TestDestroyResources:
    """Test destroy_resources function."""

    @pytest.fixture
    def args(self):
        """Create mock args fixture."""
        args = Mock()
        args.aws_account_id = '123456789012'
        args.aws_region = 'us-east-1'
        args.aws_iam_role_name = 'TestRole'
        args.github_org = 'test-org'
        args.github_repo = 'test-repo'
        args.aws_access_key_id = 'AKIATEST'
        args.aws_secret_access_key = 'secret123'
        args.force = True
        return args

    @patch('bootstrap.is_running_in_github_actions', return_value=False)
    @patch('bootstrap.AWSClientStdlib')
    def test_destroy_uses_stdlib_client_in_local_mode(self, mock_stdlib, mock_gh_check, args):
        """Test that destroy_resources uses AWSClientStdlib in local mode."""
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_client.secrets.secret_exists.return_value = True
        mock_client.secrets.delete_secret.return_value = True
        mock_client.iam.role_exists.return_value = True
        mock_client.iam.detach_managed_policy.return_value = True
        mock_client.iam.delete_role_policy.return_value = True
        mock_client.iam.delete_role.return_value = True
        mock_client.iam.oidc_provider_exists.return_value = True
        mock_client.iam.delete_oidc_provider.return_value = True

        result = bootstrap.destroy_resources(args)

        assert result == 0
        mock_stdlib.assert_called_once_with('us-east-1', access_key_id='AKIATEST', secret_access_key='secret123', session_token=None, bedrock_model_id='us.anthropic.claude-haiku-4-5-20251001-v1:0')

    @patch('bootstrap.is_running_in_github_actions', return_value=True)
    @patch('bootstrap.AWSClientStdlib')
    def test_destroy_skips_non_existent_resources(self, mock_stdlib, mock_gh_check, args):
        """Test that destroy_resources skips resources that don't exist."""
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_client.secrets.secret_exists.return_value = False  # Doesn't exist
        mock_client.iam.role_exists.return_value = False  # Doesn't exist
        mock_client.iam.oidc_provider_exists.return_value = False  # Doesn't exist

        result = bootstrap.destroy_resources(args)

        assert result == 0
        mock_client.secrets.delete_secret.assert_not_called()
        mock_client.iam.delete_role.assert_not_called()
        mock_client.iam.delete_oidc_provider.assert_not_called()

    @patch('bootstrap.is_running_in_github_actions', return_value=False)
    @patch('bootstrap.AWSClientStdlib')
    @patch('builtins.input', return_value='n')
    def test_destroy_aborts_when_user_declines_confirmation(self, mock_input, mock_stdlib, mock_gh_check, args):
        """Test that destroy_resources aborts when user declines confirmation."""
        args.force = False
        mock_client = Mock()
        mock_stdlib.return_value = mock_client

        result = bootstrap.destroy_resources(args)

        assert result == 1
        mock_client.secrets.delete_secret.assert_not_called()

    @patch('bootstrap.is_running_in_github_actions', return_value=False)
    @patch('bootstrap.AWSClientStdlib')
    def test_destroy_returns_error_when_secret_deletion_fails(self, mock_stdlib, mock_gh_check, args):
        """Test that destroy_resources returns error when secret deletion fails."""
        mock_client = Mock()
        mock_stdlib.return_value = mock_client
        mock_client.secrets.secret_exists.return_value = True
        mock_client.secrets.delete_secret.return_value = False  # Fails

        result = bootstrap.destroy_resources(args)

        assert result == 1


class TestDeleteGitHubSecrets:
    """Test delete_github_secrets function."""

    @patch('urllib.request.urlopen')
    def test_delete_github_secrets_returns_true_on_success(self, mock_urlopen):
        """Test delete_github_secrets returns True when all secrets deleted."""
        mock_response = MagicMock()
        mock_response.status = 204
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = bootstrap.delete_github_secrets(
            'ghp_test123',
            'test-org',
            'test-repo',
            ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
        )

        assert result is True
        assert mock_urlopen.call_count == 2  # Two secrets

    @patch('urllib.request.urlopen')
    def test_delete_github_secrets_handles_404_gracefully(self, mock_urlopen):
        """Test delete_github_secrets handles 404 (already deleted) gracefully."""
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 404, 'Not Found', {}, BytesIO(b'Not Found'))
        mock_urlopen.side_effect = error

        result = bootstrap.delete_github_secrets(
            'ghp_test123',
            'test-org',
            'test-repo',
            ['AWS_ACCESS_KEY_ID']
        )

        assert result is True  # 404 is considered success (already deleted)

    @patch('urllib.request.urlopen')
    def test_delete_github_secrets_returns_false_on_error(self, mock_urlopen):
        """Test delete_github_secrets returns False on non-404 errors."""
        from urllib.error import HTTPError
        from io import BytesIO
        error = HTTPError('url', 500, 'Internal Server Error', {}, BytesIO(b'Error'))
        mock_urlopen.side_effect = error

        result = bootstrap.delete_github_secrets(
            'ghp_test123',
            'test-org',
            'test-repo',
            ['AWS_ACCESS_KEY_ID']
        )

        assert result is False

    @patch('urllib.request.urlopen')
    def test_delete_github_secrets_sends_correct_request(self, mock_urlopen):
        """Test delete_github_secrets sends correct HTTP request."""
        mock_response = MagicMock()
        mock_response.status = 204
        mock_urlopen.return_value.__enter__.return_value = mock_response

        bootstrap.delete_github_secrets(
            'ghp_test123',
            'test-org',
            'test-repo',
            ['AWS_ACCESS_KEY_ID']
        )

        # Verify request was made
        call_args = mock_urlopen.call_args
        request = call_args[0][0]

        assert request.get_method() == 'DELETE'
        assert 'test-org/test-repo' in request.full_url
        assert 'AWS_ACCESS_KEY_ID' in request.full_url
        assert request.headers['Authorization'] == 'Bearer ghp_test123'
        assert request.headers['Accept'] == 'application/vnd.github+json'


class TestMainFunction:
    """Test main entry point."""

    @patch('sys.argv', ['bootstrap.py'])
    def test_main_shows_help_when_no_args(self):
        """Test main shows help when called with no arguments."""
        result = bootstrap.main()
        assert result == 1

    @patch('sys.argv', ['bootstrap.py', '--verbose', 'create',
                        '--aws-account-id', '123456789012',
                        '--aws-region', 'us-east-1',
                        '--aws-iam-role-name', 'TestRole',
                        '--github-org', 'test-org',
                        '--github-repo', 'test-repo',
                        '--aws-access-key-id', 'AKIATEST',
                        '--aws-secret-access-key', 'secret',
                        '--github-token', 'ghp_test123'])
    @patch('bootstrap.create_resources')
    def test_main_sets_debug_level_with_verbose_flag(self, mock_create):
        """Test --verbose flag sets DEBUG log level."""
        import logging
        mock_create.return_value = 0

        with patch('sys.exit'):
            bootstrap.main()

        assert logging.getLogger().level == logging.DEBUG

    @patch('sys.argv', ['bootstrap.py', '--quiet', 'create',
                        '--aws-account-id', '123456789012',
                        '--aws-region', 'us-east-1',
                        '--aws-iam-role-name', 'TestRole',
                        '--github-org', 'test-org',
                        '--github-repo', 'test-repo',
                        '--aws-access-key-id', 'AKIATEST',
                        '--aws-secret-access-key', 'secret',
                        '--github-token', 'ghp_test123'])
    @patch('bootstrap.create_resources')
    def test_main_sets_error_level_with_quiet_flag(self, mock_create):
        """Test --quiet flag sets ERROR log level."""
        import logging
        mock_create.return_value = 0

        with patch('sys.exit'):
            bootstrap.main()

        assert logging.getLogger().level == logging.ERROR

    @patch('sys.argv', ['bootstrap.py', 'destroy',
                        '--aws-account-id', '123456789012',
                        '--aws-region', 'us-east-1',
                        '--aws-iam-role-name', 'TestRole',
                        '--github-org', 'test-org',
                        '--github-repo', 'test-repo',
                        '--aws-access-key-id', 'AKIATEST',
                        '--aws-secret-access-key', 'secret',
                        '--force'])
    @patch('bootstrap.destroy_resources')
    def test_main_calls_destroy_with_force_flag(self, mock_destroy):
        """Test main calls destroy_resources with --force."""
        mock_destroy.return_value = 0

        with patch('sys.exit'):
            bootstrap.main()

        mock_destroy.assert_called_once()
        args = mock_destroy.call_args[0][0]
        assert args.force is True
#!/usr/bin/env python3
"""
Unit tests for validation functions in bootstrap.py

Tests the three validation functions that check credentials/permissions:
- validate_aws_credentials()
- validate_github_pat()
- validate_oidc_role_permissions()

These tests use mocks and verify FATAL behavior (sys.exit).
"""

import json
import sys
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path

import pytest

# Add src/bootstrap to path
REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / 'src' / 'bootstrap'))

import bootstrap


class TestValidateAWSCredentials:
    """Test validate_aws_credentials function."""

    def test_validates_sts_authentication_with_stdlib(self):
        """Test STS GetCallerIdentity check works with stdlib client."""
        mock_client = Mock()
        mock_client.validate_access = Mock(return_value=None)

        # Should not raise - validation passes
        bootstrap.validate_aws_credentials(mock_client)

        # Verify validate_access was called
        mock_client.validate_access.assert_called_once()

    def test_fails_on_invalid_credentials_stdlib(self):
        """Test sys.exit(1) on authentication failure with stdlib."""
        import urllib.error
        from io import BytesIO

        mock_client = Mock()
        # Create AWSHTTPError wrapping the original error
        original_error = urllib.error.HTTPError('url', 403, 'Forbidden', {}, BytesIO(b'Forbidden'))
        error = bootstrap.AWSHTTPError(original_error, 'Access Denied')
        mock_client.validate_access = Mock(side_effect=error)

        with pytest.raises(SystemExit) as exc_info:
            bootstrap.validate_aws_credentials(mock_client)

        assert exc_info.value.code == 1

class TestValidateGitHubPAT:
    """Test validate_github_pat function."""

    @patch('bootstrap.urllib.request.urlopen')
    def test_validates_admin_org_scope(self, mock_urlopen):
        """Test admin:org scope validation passes."""
        mock_response = MagicMock()
        mock_response.headers.get.return_value = 'admin:org, repo, workflow'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Should not raise
        bootstrap.validate_github_pat('ghp_test123')

        # Verify API call was made
        mock_urlopen.assert_called_once()

    @patch('bootstrap.urllib.request.urlopen')
    def test_validates_repo_scope(self, mock_urlopen):
        """Test repo scope validation passes."""
        mock_response = MagicMock()
        mock_response.headers.get.return_value = 'admin:org, repo'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Should not raise
        bootstrap.validate_github_pat('ghp_test123')

    @patch('bootstrap.urllib.request.urlopen')
    def test_fails_on_missing_admin_org_scope(self, mock_urlopen):
        """Test sys.exit(1) on missing admin:org scope."""
        mock_response = MagicMock()
        # Only has repo scope, missing admin:org
        mock_response.headers.get.return_value = 'repo, workflow'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with pytest.raises(SystemExit) as exc_info:
            bootstrap.validate_github_pat('ghp_test123')

        assert exc_info.value.code == 1

    @patch('bootstrap.urllib.request.urlopen')
    def test_fails_on_missing_repo_scope(self, mock_urlopen):
        """Test sys.exit(1) on missing repo scope."""
        mock_response = MagicMock()
        # Only has admin:org scope, missing repo
        mock_response.headers.get.return_value = 'admin:org, workflow'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with pytest.raises(SystemExit) as exc_info:
            bootstrap.validate_github_pat('ghp_test123')

        assert exc_info.value.code == 1

    @patch('bootstrap.urllib.request.urlopen')
    def test_fails_on_missing_both_scopes(self, mock_urlopen):
        """Test sys.exit(1) on missing both required scopes."""
        mock_response = MagicMock()
        mock_response.headers.get.return_value = 'workflow, gist'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        with pytest.raises(SystemExit) as exc_info:
            bootstrap.validate_github_pat('ghp_test123')

        assert exc_info.value.code == 1

    @patch('bootstrap.urllib.request.urlopen')
    def test_fails_on_invalid_token(self, mock_urlopen):
        """Test sys.exit(1) on 401 Unauthorized response."""
        from urllib.error import HTTPError

        mock_urlopen.side_effect = HTTPError(
            'https://api.github.com/user',
            401,
            'Unauthorized',
            {},
            None
        )

        with pytest.raises(SystemExit) as exc_info:
            bootstrap.validate_github_pat('ghp_invalid')

        assert exc_info.value.code == 1

    @patch('bootstrap.urllib.request.urlopen')
    def test_fails_on_network_error(self, mock_urlopen):
        """Test sys.exit(1) on network error."""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError("Network error")

        with pytest.raises(SystemExit) as exc_info:
            bootstrap.validate_github_pat('ghp_test123')

        assert exc_info.value.code == 1


class TestValidateOIDCRolePermissions:
    """Test validate_oidc_role_permissions function."""

    def test_validates_power_user_access_attached(self):
        """Test PowerUserAccess policy check passes when attached."""
        mock_client = Mock()
        mock_client.iam.managed_policy_attached = Mock(return_value=True)
        mock_client.run = Mock(return_value=Mock(returncode=0))

        # Should not raise
        bootstrap.validate_oidc_role_permissions(mock_client, 'TestRole')

        # Verify PowerUserAccess check was made
        mock_client.iam.managed_policy_attached.assert_called_once_with(
            'TestRole',
            'arn:aws:iam::aws:policy/PowerUserAccess'
        )

    def test_fails_on_missing_power_user_access(self):
        """Test sys.exit(1) when PowerUserAccess policy not attached."""
        mock_client = Mock()
        mock_client.iam.managed_policy_attached = Mock(return_value=False)

        with pytest.raises(SystemExit) as exc_info:
            bootstrap.validate_oidc_role_permissions(mock_client, 'TestRole')

        assert exc_info.value.code == 1

    def test_validates_iam_role_management_policy_with_stdlib(self):
        """Test IAMRoleManagement inline policy check with stdlib."""
        mock_client = Mock()
        mock_client.iam.managed_policy_attached = Mock(return_value=True)
        mock_client.iam.inline_policy_exists = Mock(return_value=True)

        # Should not raise
        bootstrap.validate_oidc_role_permissions(mock_client, 'TestRole')

        # Verify inline policy check was made
        mock_client.iam.inline_policy_exists.assert_called_once_with('TestRole', 'IAMRoleManagement')

    def test_fails_on_missing_inline_policy_with_stdlib(self):
        """Test sys.exit(1) when IAMRoleManagement policy missing (stdlib)."""
        mock_client = Mock()
        mock_client.iam.managed_policy_attached = Mock(return_value=True)
        mock_client.iam.inline_policy_exists = Mock(return_value=False)

        with pytest.raises(SystemExit) as exc_info:
            bootstrap.validate_oidc_role_permissions(mock_client, 'TestRole')

        assert exc_info.value.code == 1


class TestClassHierarchy:
    """Test class inheritance structure for refactored AWS clients."""

    def test_iam_client_inherits_from_base(self):
        """Test that IAMClient inherits from AWSClientBase."""
        client = bootstrap.IAMClient('us-east-1', 'AKIATEST', 'secret')
        assert isinstance(client, bootstrap.AWSClientBase)
        assert client.region == 'us-east-1'
        assert client.access_key_id == 'AKIATEST'
        assert client.secret_access_key == 'secret'

    def test_secrets_manager_client_inherits_from_base(self):
        """Test that SecretsManagerClient inherits from AWSClientBase."""
        client = bootstrap.SecretsManagerClient('us-east-1', 'AKIATEST', 'secret')
        assert isinstance(client, bootstrap.AWSClientBase)
        assert client.region == 'us-east-1'
        assert client.access_key_id == 'AKIATEST'

    def test_sts_client_inherits_from_base(self):
        """Test that STSClient inherits from AWSClientBase."""
        client = bootstrap.STSClient('us-east-1', 'AKIATEST', 'secret')
        assert isinstance(client, bootstrap.AWSClientBase)
        assert client.region == 'us-east-1'
        assert client.access_key_id == 'AKIATEST'
        assert client.secret_access_key == 'secret'

    def test_base_client_has_signing_methods(self):
        """Test that AWSClientBase has AWS Signature V4 signing infrastructure."""
        client = bootstrap.AWSClientBase('us-east-1', 'AKIATEST', 'secret')

        # Verify signing infrastructure methods exist
        assert hasattr(client, '_add_aws_signing_headers_with_timestamp')
        assert hasattr(client, '_build_canonical_request_string')
        assert hasattr(client, '_build_string_to_sign_with_credential_scope')
        assert hasattr(client, '_calculate_aws_signature_v4_hmac_chain')
        assert hasattr(client, '_build_aws_authorization_header')
        assert hasattr(client, '_sign_request')
        assert hasattr(client, '_prepare_json_api_request_with_signing')
        assert hasattr(client, '_prepare_query_api_request_with_signing')
        assert hasattr(client, '_make_request')

    def test_canonical_request_url_encodes_uri_segments(self):
        """Test that canonical request URL-encodes special chars in URI per AWS SigV4."""
        client = bootstrap.AWSClientBase('us-east-1', 'AKIATEST', 'secret')

        # Test with URI containing special characters (like Bedrock model IDs with colons)
        canonical_request, _ = client._build_canonical_request_string(
            'POST',
            request_components={
                'uri': '/model/anthropic.claude-sonnet-4-5-20250929-v1:0/invoke',
                'query': '',
                'headers': {'host': 'bedrock-runtime.us-east-1.amazonaws.com'},
                'payload': b'test payload'
            }
        )

        # Verify colons are URL-encoded as %3A in canonical URI
        assert '/model/anthropic.claude-sonnet-4-5-20250929-v1%3A0/invoke' in canonical_request
        # Verify slashes and dots are NOT encoded (path separators and valid chars)
        assert canonical_request.startswith('POST\n/model/anthropic')


class TestContainerUtilityMethods:
    """Test utility methods on AWSClientStdlib container."""

    def test_container_has_utility_methods(self):
        """Test that AWSClientStdlib has utility methods."""
        client = bootstrap.AWSClientStdlib('us-east-1', 'AKIATEST', 'secret')

        assert callable(client.get_account_id)
        assert callable(client.validate_access)

    def test_get_account_id_delegates_to_sts_client(self):
        """Test that get_account_id delegation exists."""
        client = bootstrap.AWSClientStdlib('us-east-1', 'AKIATEST', 'secret')

        assert hasattr(client, 'get_account_id')
        assert hasattr(client.sts, 'get_account_id')

    def test_validate_access_consolidates_service_checks(self):
        """Test that validate_access consolidates service validation."""
        client = bootstrap.AWSClientStdlib('us-east-1', 'AKIATEST', 'secret')

        # Verify validate_access is a single method that tests all services
        assert callable(client.validate_access)

        # Verify individual service test methods exist on specialized clients
        assert callable(client.sts.test_sts_access)
        assert callable(client.iam.test_iam_access)
        assert callable(client.secrets.test_secrets_manager_access)


class TestBedrockClient:
    """Test BedrockClient methods."""

    @pytest.fixture
    def bedrock_client(self):
        """Create BedrockClient fixture."""
        return bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret123')

    @patch('urllib.request.urlopen')
    def test_invoke_model_success_anthropic(self, mock_urlopen):
        """Test invoke_model returns Claude response with Anthropic model."""
        # Create client with Anthropic model
        bedrock_client = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret123',
                                                   model_id='anthropic.claude-sonnet-4-5-20250929-v1:0')

        response_data = {
            'content': [{'text': 'Test response from Claude'}]
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = bedrock_client.invoke_model('Test prompt')

        assert result == 'Test response from Claude'

    @patch('urllib.request.urlopen')
    def test_invoke_model_success_amazon_nova(self, mock_urlopen):
        """Test invoke_model returns response with Amazon Nova model."""
        # Create client with Amazon Nova model
        bedrock_client = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret123',
                                                   model_id='amazon.nova-micro-v1:0')

        response_data = {
            'output': {'message': {'content': [{'text': 'Test response from Nova'}]}}
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = bedrock_client.invoke_model('Test prompt')

        assert result == 'Test response from Nova'

    def test_bedrock_client_inherits_from_base(self):
        """Test that BedrockClient inherits from AWSClientBase."""
        client = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        assert isinstance(client, bootstrap.AWSClientBase)
        assert client.region == 'us-east-1'
        assert client.access_key_id == 'AKIATEST'

    @patch.object(bootstrap.BedrockClient, '_make_request')
    def test_enable_model_access_uses_rest_api_format(self, mock_request):
        """Test enable_model_access uses REST API format (path+body) not JSON-RPC (params) for Anthropic models."""
        # Create client with Anthropic model (these tests are for Anthropic-specific flow)
        bedrock_client = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret123',
                                                   model_id='anthropic.claude-sonnet-4-5-20250929-v1:0')
        # Mock successful responses for all 3 steps
        mock_request.side_effect = [
            '{}',  # Step 1: PutUseCaseForModelAccess
            '{"offers": [{"offerToken": "token123"}]}',  # Step 2: ListFoundationModelAgreementOffers
            '{}',  # Step 2: CreateFoundationModelAgreement
            '{}'   # Step 3: FoundationModelEntitlement
        ]

        result = bedrock_client.enable_model_access()

        assert result is True
        # Verify 4 API calls (use case, list offers, create agreement, entitlement)
        assert len(mock_request.call_args_list) == 4

        # Verify all calls use REST API format (path + body), NOT JSON-RPC (params + use_json)
        for call in mock_request.call_args_list:
            args, kwargs = call
            # REST API must have 'path' and 'body' kwargs
            assert 'path' in kwargs, f"Missing 'path' - should use REST API format, not JSON-RPC: {call}"
            assert 'body' in kwargs, f"Missing 'body' - should use REST API format, not JSON-RPC: {call}"
            # Should NOT have use_json=True (that's for JSON-RPC APIs)
            assert kwargs.get('use_json') is not True, f"Should not use use_json=True for REST APIs: {call}"

    @patch.object(bootstrap.BedrockClient, '_make_request')
    def test_enable_model_access_idempotent_on_already_exists(self, mock_request, bedrock_client):
        """Test enable_model_access handles already submitted use case gracefully."""
        from io import BytesIO
        # Use case already submitted
        error = bootstrap.AWSHTTPError(
            urllib.error.HTTPError('url', 400, 'Bad Request', {}, BytesIO(b'')),
            '{"message": "Use case already exists"}'
        )
        mock_request.side_effect = [
            error,  # PutUseCaseForModelAccess fails (already exists)
            '{"offers": []}',  # ListFoundationModelAgreementOffers (no offers, already accepted)
            '{}'  # FoundationModelEntitlement
        ]

        result = bedrock_client.enable_model_access()

        assert result is True  # Should succeed (idempotent)

    @patch.object(bootstrap.BedrockClient, '_make_request')
    def test_enable_model_access_accepts_agreement(self, mock_request):
        """Test enable_model_access accepts model agreement for Anthropic models."""
        # Create client with Anthropic model
        bedrock_client = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret123',
                                                   model_id='anthropic.claude-sonnet-4-5-20250929-v1:0')
        mock_request.side_effect = [
            '{}',  # PutUseCaseForModelAccess
            '{"offers": [{"offerToken": "token123"}]}',  # ListFoundationModelAgreementOffers
            '{}',  # CreateFoundationModelAgreement
            '{}'   # FoundationModelEntitlement
        ]

        result = bedrock_client.enable_model_access()

        assert result is True
        # Verify CreateFoundationModelAgreement was called with token
        create_agreement_call = [call for call in mock_request.call_args_list
                                if 'CreateFoundationModelAgreement' in str(call)]
        assert len(create_agreement_call) == 1

    @patch.object(bootstrap.BedrockClient, '_make_request')
    def test_enable_model_access_fails_on_account_not_authorized(self, mock_request):
        """Test enable_model_access fails when account not authorized (requires support case) for Anthropic models."""
        # Create client with Anthropic model
        bedrock_client = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret123',
                                                   model_id='anthropic.claude-sonnet-4-5-20250929-v1:0')
        from io import BytesIO
        # Account needs manual verification
        error = bootstrap.AWSHTTPError(
            urllib.error.HTTPError('url', 400, 'Bad Request', {}, BytesIO(b'')),
            '{"message":"Your account is not authorized to perform this action. Please create a support case"}'
        )
        mock_request.side_effect = [
            '{}',  # PutUseCaseForModelAccess
            '{"offers": []}',  # ListFoundationModelAgreementOffers
            error  # FoundationModelEntitlement fails (not authorized)
        ]

        result = bedrock_client.enable_model_access()

        assert result is False  # Should fail loudly, not silently succeed

    def test_enable_model_access_skips_for_non_anthropic_models(self):
        """Test enable_model_access skips the access setup for non-Anthropic models like Amazon Nova."""
        # Amazon Nova models don't require the access setup process
        bedrock_client = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret123',
                                                   model_id='amazon.nova-micro-v1:0')

        # Should return True without making any API calls
        result = bedrock_client.enable_model_access()

        assert result is True

    def test_bedrock_client_accepts_custom_model_id(self):
        """Test BedrockClient accepts custom model_id parameter."""
        client = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret123',
                                          model_id='amazon.nova-micro-v1:0')
        assert client.model_id == 'amazon.nova-micro-v1:0'

        client2 = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret123',
                                           model_id='anthropic.claude-sonnet-4-5-20250929-v1:0')
        assert client2.model_id == 'anthropic.claude-sonnet-4-5-20250929-v1:0'

    def test_bedrock_client_defaults_to_claude_haiku(self):
        """Test BedrockClient defaults to Claude Haiku 4.5."""
        client = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret123')
        assert client.model_id == 'us.anthropic.claude-haiku-4-5-20251001-v1:0'

    @patch('urllib.request.urlopen')
    def test_invoke_model_caps_max_tokens_for_amazon_nova(self, mock_urlopen):
        """Test invoke_model caps max_tokens at 10240 for Amazon Nova models."""
        bedrock_client = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret123',
                                                   model_id='amazon.nova-micro-v1:0')

        response_data = {
            'output': {'message': {'content': [{'text': 'Test response'}]}}
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Request 16000 tokens (exceeds Nova limit)
        result = bedrock_client.invoke_model('Test prompt', max_tokens=16000)

        # Verify it was capped at 10240
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode('utf-8'))
        assert body['inferenceConfig']['max_new_tokens'] == 10240
        assert result == 'Test response'

    @patch('urllib.request.urlopen')
    def test_invoke_model_uses_claude_4_format_for_anthropic(self, mock_urlopen):
        """Test invoke_model uses Claude 4+ request format for Anthropic models."""
        bedrock_client = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret123',
                                                   model_id='us.anthropic.claude-haiku-4-5-20251001-v1:0')

        response_data = {
            'content': [{'text': 'Test response'}]
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = bedrock_client.invoke_model('Test prompt', max_tokens=1000)

        # Verify Claude 4+ format: content must be array with type/text structure
        call_args = mock_urlopen.call_args
        request = call_args[0][0]
        body = json.loads(request.data.decode('utf-8'))
        assert 'messages' in body
        assert len(body['messages']) == 1
        assert body['messages'][0]['role'] == 'user'
        assert isinstance(body['messages'][0]['content'], list)
        assert len(body['messages'][0]['content']) == 1
        assert body['messages'][0]['content'][0]['type'] == 'text'
        assert body['messages'][0]['content'][0]['text'] == 'Test prompt'
        assert body['anthropic_version'] == 'bedrock-2023-05-31'
        assert body['max_tokens'] == 1000
        assert result == 'Test response'


class TestReadmeHelperFunctions:
    """Test README helper functions."""

    @patch('bootstrap.assume_role_with_oidc')
    @patch('bootstrap.is_running_in_github_actions')
    @patch('bootstrap.detect_bootstrap_state')
    def test_get_credentials_for_state_oidc(self, mock_state, mock_is_gha, mock_oidc):
        """Test _get_credentials_for_state uses OIDC in warm state."""
        mock_state.return_value = 'warm'
        mock_is_gha.return_value = True
        mock_oidc.return_value = {
            'access_key_id': 'AKIAOIDC',
            'secret_access_key': 'secret',
            'session_token': 'token'
        }

        args = MagicMock()
        args.aws_account_id = '123456789012'
        args.aws_region = 'us-east-1'
        args.aws_iam_role_name = 'TestRole'

        access_key, secret_key, session_token = bootstrap._get_credentials_for_state(args)

        assert access_key == 'AKIAOIDC'
        assert session_token == 'token'
        mock_oidc.assert_called_once()

    @patch('bootstrap.is_running_in_github_actions')
    @patch('bootstrap.detect_bootstrap_state')
    def test_get_credentials_for_state_direct_credentials(self, mock_state, mock_is_gha):
        """Test _get_credentials_for_state uses direct credentials in cold state."""
        mock_state.return_value = 'cold'
        mock_is_gha.return_value = False

        args = MagicMock()
        args.aws_account_id = '123456789012'
        args.aws_region = 'us-east-1'
        args.aws_iam_role_name = 'TestRole'
        args.aws_access_key_id = 'AKIADIRECT'
        args.aws_secret_access_key = 'secretdirect'

        access_key, secret_key, session_token = bootstrap._get_credentials_for_state(args)

        assert access_key == 'AKIADIRECT'
        assert secret_key == 'secretdirect'
        assert session_token is None

    @patch.object(bootstrap.BedrockClient, 'invoke_model')
    def test_check_readme_needs_update_returns_true(self, mock_invoke):
        """Test _check_readme_needs_update returns True when update needed."""
        mock_invoke.return_value = 'true'

        bedrock = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        result = bootstrap._check_readme_needs_update(bedrock, 'code', 'readme')

        assert result is True
        mock_invoke.assert_called_once()

    @patch.object(bootstrap.BedrockClient, 'invoke_model')
    def test_check_readme_needs_update_returns_false(self, mock_invoke):
        """Test _check_readme_needs_update returns False when current."""
        mock_invoke.return_value = 'false'

        bedrock = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        result = bootstrap._check_readme_needs_update(bedrock, 'code', 'readme')

        assert result is False

    @patch.object(bootstrap.BedrockClient, 'invoke_model')
    def test_check_readme_needs_update_propagates_exception(self, mock_invoke):
        """Test _check_readme_needs_update propagates exceptions."""
        mock_invoke.side_effect = Exception('Bedrock error')

        bedrock = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret')

        with pytest.raises(Exception, match='Bedrock error'):
            bootstrap._check_readme_needs_update(bedrock, 'code', 'readme')

    @patch.object(bootstrap.BedrockClient, 'invoke_model')
    def test_check_readme_needs_update_empty_readme(self, mock_invoke):
        """Test _check_readme_needs_update returns True when README is empty."""
        bedrock = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret')

        # Empty string
        result = bootstrap._check_readme_needs_update(bedrock, 'code', '')
        assert result is True
        mock_invoke.assert_not_called()

        # Whitespace only
        result = bootstrap._check_readme_needs_update(bedrock, 'code', '   \n\t  ')
        assert result is True
        assert mock_invoke.call_count == 0  # Still not called

    @patch.object(bootstrap.BedrockClient, 'invoke_model')
    def test_update_readme_success(self, mock_invoke):
        """Test _update_readme returns generated README."""
        mock_invoke.return_value = '# New README\nContent here'

        bedrock = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret')
        result = bootstrap._update_readme(bedrock, 'code')

        assert result == '# New README\nContent here'
        mock_invoke.assert_called_once()

    @patch.object(bootstrap.BedrockClient, 'invoke_model')
    def test_update_readme_raises_on_exception(self, mock_invoke):
        """Test _update_readme raises exception on failure."""
        mock_invoke.side_effect = Exception('Bedrock error')

        bedrock = bootstrap.BedrockClient('us-east-1', 'AKIATEST', 'secret')

        with pytest.raises(Exception):
            bootstrap._update_readme(bedrock, 'code')


class TestReadmeCommand:
    """Test cmd_readme function."""

    @patch('bootstrap._check_readme_needs_update')
    @patch('bootstrap.BedrockClient')
    @patch('bootstrap._get_credentials_for_state')
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_cmd_readme_check_update_needed(self, mock_exists, mock_open, mock_creds,
                                           mock_bedrock_class, mock_check):
        """Test cmd_readme --check returns 0 when update needed."""
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_check.return_value = True
        mock_exists.return_value = True

        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = 'code content'
        mock_open.return_value = mock_file

        args = MagicMock()
        args.check = True
        args.update = False
        args.aws_region = 'us-east-1'
        args.output_file = None

        result = bootstrap.cmd_readme(args)

        assert result == 0
        mock_check.assert_called_once()

    @patch('bootstrap._check_readme_needs_update')
    @patch('bootstrap.BedrockClient')
    @patch('bootstrap._get_credentials_for_state')
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_cmd_readme_check_no_update_needed(self, mock_exists, mock_open, mock_creds,
                                               mock_bedrock_class, mock_check):
        """Test cmd_readme --check returns 0 when no update needed."""
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_check.return_value = False
        mock_exists.return_value = True

        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = 'code content'
        mock_open.return_value = mock_file

        args = MagicMock()
        args.check = True
        args.update = False
        args.aws_region = 'us-east-1'
        args.output_file = None

        result = bootstrap.cmd_readme(args)

        assert result == 0

    @patch('bootstrap._update_readme')
    @patch('bootstrap.BedrockClient')
    @patch('bootstrap._get_credentials_for_state')
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_cmd_readme_update_success(self, mock_exists, mock_open, mock_creds,
                                       mock_bedrock_class, mock_update):
        """Test cmd_readme --update writes README successfully."""
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_update.return_value = '# New README'
        mock_exists.return_value = False

        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = 'code content'
        mock_open.return_value = mock_file

        args = MagicMock()
        args.check = False
        args.update = True
        args.aws_region = 'us-east-1'

        result = bootstrap.cmd_readme(args)

        assert result == 0
        mock_update.assert_called_once()

    @patch('bootstrap._get_credentials_for_state')
    def test_cmd_readme_fails_without_credentials(self, mock_creds):
        """Test cmd_readme returns 1 when credentials unavailable."""
        mock_creds.return_value = (None, None, None)

        args = MagicMock()
        args.check = True
        args.aws_region = 'us-east-1'

        result = bootstrap.cmd_readme(args)

        assert result == 1

    @patch('bootstrap._check_readme_needs_update')
    @patch('bootstrap.BedrockClient')
    @patch('bootstrap._get_credentials_for_state')
    @patch('builtins.open', create=True)
    @patch('os.path.exists')
    def test_cmd_readme_propagates_bedrock_errors(self, mock_exists, mock_open, mock_creds,
                                                   mock_bedrock_class, mock_check):
        """Test cmd_readme propagates exceptions from Bedrock (like 403 errors)."""
        from urllib.error import HTTPError
        from io import BytesIO

        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_exists.return_value = True

        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = 'code content'
        mock_open.return_value = mock_file

        # Simulate Bedrock 403 error
        error = HTTPError('url', 403, 'Forbidden', {}, BytesIO(b'Access Denied'))
        mock_check.side_effect = error

        args = MagicMock()
        args.check = True
        args.update = False
        args.aws_region = 'us-east-1'

        # Verify exception propagates instead of being caught
        with pytest.raises(HTTPError, match='Forbidden'):
            bootstrap.cmd_readme(args)

    @patch('bootstrap._check_readme_needs_update')
    @patch('bootstrap.BedrockClient')
    @patch('bootstrap._get_credentials_for_state')
    def test_cmd_readme_writes_to_output_file_when_update_needed(self, mock_creds,
                                                                  mock_bedrock_class,
                                                                  mock_check, tmp_path, monkeypatch):
        """Test cmd_readme writes should_update=true to output file when update needed."""
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_check.return_value = True

        # Create real temp files
        bootstrap_file = tmp_path / "bootstrap.py"
        bootstrap_file.write_text("code content")
        readme_file = tmp_path / "README.md"
        readme_file.write_text("readme content")
        output_file = tmp_path / "output.txt"

        # Patch the file paths
        monkeypatch.setattr('bootstrap.os.path.abspath', lambda x: str(bootstrap_file))

        args = MagicMock()
        args.check = True
        args.update = False
        args.aws_region = 'us-east-1'
        args.output_file = str(output_file)

        result = bootstrap.cmd_readme(args)

        assert result == 0
        assert output_file.read_text() == 'should_update=true\n'

    @patch('bootstrap._check_readme_needs_update')
    @patch('bootstrap.BedrockClient')
    @patch('bootstrap._get_credentials_for_state')
    def test_cmd_readme_writes_to_output_file_when_no_update_needed(self, mock_creds,
                                                                     mock_bedrock_class,
                                                                     mock_check, tmp_path, monkeypatch):
        """Test cmd_readme writes should_update=false to output file when no update needed."""
        mock_creds.return_value = ('AKIATEST', 'secret', None)
        mock_check.return_value = False

        # Create real temp files
        bootstrap_file = tmp_path / "bootstrap.py"
        bootstrap_file.write_text("code content")
        readme_file = tmp_path / "README.md"
        readme_file.write_text("readme content")
        output_file = tmp_path / "output.txt"

        # Patch the file paths
        monkeypatch.setattr('bootstrap.os.path.abspath', lambda x: str(bootstrap_file))

        args = MagicMock()
        args.check = True
        args.update = False
        args.aws_region = 'us-east-1'
        args.output_file = str(output_file)

        result = bootstrap.cmd_readme(args)

        assert result == 0
        assert output_file.read_text() == 'should_update=false\n'


class TestIAMPolicyWithBedrock:
    """Test IAM policy includes Bedrock permissions."""

    def test_create_iam_role_management_policy_includes_bedrock(self):
        """Test IAM policy includes Bedrock permissions for README and model access."""
        policy = bootstrap.create_iam_role_management_policy()

        # Policy now has 3 statements: IAM, Bedrock control plane, Bedrock InvokeModel
        assert len(policy['Statement']) == 3

        # Find all Bedrock actions across statements
        all_actions = []
        for statement in policy['Statement']:
            all_actions.extend(statement['Action'])

        # Control plane permissions (statement 1)
        assert 'bedrock:ListFoundationModels' in all_actions
        assert 'bedrock:PutUseCaseForModelAccess' in all_actions
        assert 'bedrock:ListFoundationModelAgreementOffers' in all_actions
        assert 'bedrock:CreateFoundationModelAgreement' in all_actions

        # InvokeModel with explicit model ARNs (statement 3)
        invoke_statement = [s for s in policy['Statement'] if 'bedrock:InvokeModel' in s['Action']][0]
        assert isinstance(invoke_statement['Resource'], list)
        assert 'arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0' in invoke_statement['Resource']
        assert 'arn:aws:bedrock:us-east-1::foundation-model/openai.gpt-oss-120b-1:0' in invoke_statement['Resource']
