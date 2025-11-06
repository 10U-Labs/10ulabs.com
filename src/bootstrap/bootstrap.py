#!/usr/bin/env python3
import argparse
import hashlib
import hmac
import json
import logging
import os
import random
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional, Dict, Any
from urllib.parse import quote, unquote
import urllib.request
import urllib.error
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stderr
)
class AWSHTTPError(Exception):
    def __init__(self, original_error: urllib.error.HTTPError, error_body: str):
        self.original_error = original_error
        self.error_body = error_body
        self.code = original_error.code
        self.reason = original_error.msg
        super().__init__(f"AWS API error {original_error.code}: {original_error.msg}")
def is_running_in_github_actions() -> bool:
    return os.environ.get('GITHUB_ACTIONS', '').lower() == 'true'
def detect_bootstrap_state(account_id: str, region: str, role_name: str,
                          access_key_id: Optional[str] = None,
                          secret_access_key: Optional[str] = None) -> str:
    """Detect current bootstrap state.
    Args:
        account_id: AWS account ID
        region: AWS region
        role_name: IAM role name
        access_key_id: AWS access key ID (optional, will use environment if not provided)
        secret_access_key: AWS secret access key (optional, will use environment if not provided)
    Returns:
        'cold' - No infrastructure exists (State 1)
        'warm' - Infrastructure exists (State 2)
    Note: Uses OIDC authentication if available, otherwise uses provided or environment credentials.
    """
    oidc_token = get_oidc_token()
    if oidc_token:
        oidc_creds = assume_role_with_oidc(account_id, region, role_name)
        if oidc_creds:
            logging.info("State: WARM (infrastructure exists, using OIDC)")
            return 'warm'
        logging.info("State: COLD (OIDC available but role doesn't exist)")
        return 'cold'
    if not access_key_id:
        access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    if not secret_access_key:
        secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    if not access_key_id or not secret_access_key:
        logging.error("No credentials available to detect state")
        return 'cold'
    try:
        iam_client = IAMClient(region, access_key_id, secret_access_key)
        if iam_client.oidc_provider_exists(account_id):
            logging.info("State: WARM (infrastructure exists, using direct credentials)")
            return 'warm'
        logging.info("State: COLD (no infrastructure, using direct credentials)")
        return 'cold'
    except (AWSHTTPError, urllib.error.URLError) as e:
        logging.warning("Failed to check OIDC provider existence: %s. Assuming cold state.", e)
        return 'cold'
def get_oidc_token() -> Optional[str]:
    token_url = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_URL')
    token_request_token = os.environ.get('ACTIONS_ID_TOKEN_REQUEST_TOKEN')
    if not token_url or not token_request_token:
        logging.debug("OIDC token not available (not in GitHub Actions with id-token: write)")
        return None
    try:
        token_url_with_audience = f"{token_url}&audience=sts.amazonaws.com"
        req = urllib.request.Request(
            token_url_with_audience,
            headers={'Authorization': f'Bearer {token_request_token}'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            return data.get('value')
    except (AWSHTTPError, urllib.error.URLError) as e:
        logging.error("Failed to get OIDC token (network error): %s", e)
        return None
    except json.JSONDecodeError as e:
        logging.error("Failed to parse OIDC token response: %s", e)
        return None
def assume_role_with_oidc(account_id: str, region: str, role_name: str) -> Optional[Dict[str, str]]:
    oidc_token = get_oidc_token()
    if not oidc_token:
        logging.error("No OIDC token available")
        return None
    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    sts_client = STSClient(region, '', '')
    creds = sts_client.assume_role_with_web_identity(role_arn, oidc_token)
    if creds:
        logging.info("Successfully assumed role: %s", role_name)
        return creds
    logging.error("Failed to assume role with OIDC")
    return None
def get_secret_from_secrets_manager(secret_name: str, region: str,
                                    access_key_id: str, secret_access_key: str,
                                    session_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve secret from AWS Secrets Manager using Python stdlib client."""
    secrets_client = SecretsManagerClient(region, access_key_id, secret_access_key, session_token)
    return secrets_client.get_secret_value(secret_name)
class AWSClientBase:  # pylint: disable=too-few-public-methods
    API_VERSIONS = {
        'iam': '2010-05-08',
        'sts': '2011-06-15',
        'secretsmanager': '2017-10-17'
    }
    def __init__(self, region: str, access_key_id: str, secret_access_key: str,
                 session_token: Optional[str] = None):
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.session_token = session_token
        self.account_id = None
    def _add_aws_signing_headers_with_timestamp(self, headers: Dict[str, str],
                                                host: str) -> tuple:
        """Add required AWS signing headers and return timestamps for signing.
        Returns:
            Tuple of (amz_date, date_stamp) for use in signature calculation
        """
        current_time = datetime.utcnow()
        amz_date = current_time.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = current_time.strftime('%Y%m%d')
        headers['X-Amz-Date'] = amz_date
        headers['Host'] = host
        if self.session_token:
            headers['X-Amz-Security-Token'] = self.session_token
        return amz_date, date_stamp
    def _build_canonical_request_string(self, method: str, *,
                                        request_components: Dict[str, Any]) -> tuple:
        """Build canonical request string per AWS Signature Version 4 specification.
        Args:
            method: HTTP method (GET, POST, etc.)
            request_components: Dict with 'uri', 'query', 'headers', 'payload'
        Returns:
            Tuple of (canonical_request, signed_headers_list)
        """
        uri = request_components['uri']
        query = request_components['query']
        headers = request_components['headers']
        payload = request_components['payload']
        uri_parts = uri.split('/')
        canonical_uri = '/'.join(quote(part, safe='') for part in uri_parts)
        canonical_headers = '\n'.join(
            f"{key.lower()}:{value.strip()}"
            for key, value in sorted(headers.items())
        ) + '\n'
        signed_headers_list = ';'.join(sorted(key.lower() for key in headers.keys()))
        payload_hash = hashlib.sha256(payload).hexdigest()
        canonical_request = (
            f"{method}\n"
            f"{canonical_uri}\n"
            f"{query}\n"
            f"{canonical_headers}\n"
            f"{signed_headers_list}\n"
            f"{payload_hash}"
        )
        return canonical_request, signed_headers_list
    def _build_string_to_sign_with_credential_scope(self, amz_date: str,
                                                    date_stamp: str,
                                                    service: str,
                                                    canonical_request: str) -> tuple:
        """Build string to sign with credential scope for AWS Signature Version 4.
        Returns:
            Tuple of (string_to_sign, credential_scope)
        """
        credential_scope = f"{date_stamp}/{self.region}/{service}/aws4_request"
        canonical_request_hash = hashlib.sha256(
            canonical_request.encode('utf-8')
        ).hexdigest()
        string_to_sign = (
            "AWS4-HMAC-SHA256\n"
            f"{amz_date}\n"
            f"{credential_scope}\n"
            f"{canonical_request_hash}"
        )
        return string_to_sign, credential_scope
    def _calculate_aws_signature_v4_hmac_chain(self, date_stamp: str,
                                               service: str,
                                               string_to_sign: str) -> str:
        """Calculate AWS Signature Version 4 using HMAC-SHA256 key derivation chain.
        Implements the AWS SigV4 signing key derivation:
        1. HMAC("AWS4" + secret_key, date)
        2. HMAC(date_key, region)
        3. HMAC(region_key, service)
        4. HMAC(service_key, "aws4_request")
        5. HMAC(signing_key, string_to_sign)
        """
        def compute_hmac_sha256(key_material: bytes, message: str) -> bytes:
            return hmac.new(key_material, message.encode('utf-8'), hashlib.sha256).digest()
        key_with_date = compute_hmac_sha256(
            f"AWS4{self.secret_access_key}".encode('utf-8'),
            date_stamp
        )
        key_with_region = compute_hmac_sha256(key_with_date, self.region)
        key_with_service = compute_hmac_sha256(key_with_region, service)
        signing_key = compute_hmac_sha256(key_with_service, "aws4_request")
        signature = hmac.new(
            signing_key,
            string_to_sign.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    def _build_aws_authorization_header(self, signature: str,
                                       credential_scope: str,
                                       signed_headers_list: str) -> str:
        """Build AWS Signature Version 4 authorization header value.
        Args:
            signature: Calculated signature hex string
            credential_scope: Credential scope (date/region/service/aws4_request)
            signed_headers_list: Semicolon-separated list of signed header names
        Returns:
            Complete Authorization header value
        """
        authorization_header = (
            f"AWS4-HMAC-SHA256 "
            f"Credential={self.access_key_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers_list}, "
            f"Signature={signature}"
        )
        return authorization_header
    def _sign_request(self, method: str, service: str, *,
                     request_data: Dict[str, Any]) -> Dict[str, str]:
        """Sign AWS API request using AWS Signature Version 4.
        Args:
            method: HTTP method (GET, POST, etc.)
            service: AWS service name
            request_data: Dict containing 'host', 'uri', 'query', 'headers', 'payload'
        """
        headers = request_data['headers']
        host = request_data['host']
        amz_date, date_stamp = self._add_aws_signing_headers_with_timestamp(
            headers, host
        )
        request_components = {
            'uri': request_data['uri'],
            'query': request_data['query'],
            'headers': headers,
            'payload': request_data['payload']
        }
        canonical_request, signed_headers_list = self._build_canonical_request_string(
            method, request_components=request_components
        )
        string_to_sign, credential_scope = self._build_string_to_sign_with_credential_scope(
            amz_date, date_stamp, service, canonical_request
        )
        signature = self._calculate_aws_signature_v4_hmac_chain(
            date_stamp, service, string_to_sign
        )
        headers['Authorization'] = self._build_aws_authorization_header(
            signature, credential_scope, signed_headers_list
        )
        return headers
    def _prepare_json_api_request_with_signing(self, service: str, action: str,
                                               host: str,
                                               params: Optional[Dict[str, Any]]) -> urllib.request.Request:
        """Prepare signed request for JSON-based AWS APIs (e.g., Secrets Manager)."""
        target = f"secretsmanager.{action}"
        params_dict = params or {}
        json_string = json.dumps(params_dict)
        payload = json_string.encode('utf-8')
        headers = {
            'Content-Type': 'application/x-amz-json-1.1',
            'X-Amz-Target': target
        }
        signed_headers = self._sign_request(
            'POST', service, request_data={
                'host': host,
                'uri': '/',
                'query': '',
                'headers': headers,
                'payload': payload
            }
        )
        return urllib.request.Request(
            f"https://{host}/",
            data=payload,
            headers=signed_headers,
            method='POST'
        )
    def _prepare_query_api_request_with_signing(self, service: str, action: str,
                                                host: str,
                                                params: Optional[Dict[str, Any]]) -> urllib.request.Request:
        """Prepare signed request for Query-based AWS APIs (e.g., IAM, STS)."""
        query_params = {'Action': action, 'Version': self.API_VERSIONS.get(service, '2010-05-08')}
        if params:
            query_params.update(params)
        encoded_pairs = []
        for key, value in sorted(query_params.items()):
            encoded_key = quote(str(key), safe='')
            encoded_value = quote(str(value), safe='')
            encoded_pairs.append(f"{encoded_key}={encoded_value}")
        query_string = '&'.join(encoded_pairs)
        payload = query_string.encode('utf-8')
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded; charset=utf-8'
        }
        signed_headers = self._sign_request(
            'POST', service, request_data={
                'host': host,
                'uri': '/',
                'query': '',
                'headers': headers,
                'payload': payload
            }
        )
        return urllib.request.Request(
            f"https://{host}/",
            data=payload,
            headers=signed_headers,
            method='POST'
        )
    def _prepare_rest_api_request_with_signing(self, service: str, host: str,
                                                path: str, body: str) -> urllib.request.Request:
        """Prepare signed request for REST-based AWS APIs (e.g., Bedrock)."""
        payload = body.encode('utf-8')
        headers = {
            'Content-Type': 'application/json'
        }
        signed_headers = self._sign_request(
            'POST', service, request_data={
                'host': host,
                'uri': path,
                'query': '',
                'headers': headers,
                'payload': payload
            }
        )
        return urllib.request.Request(
            f"https://{host}{path}",
            data=payload,
            headers=signed_headers,
            method='POST'
        )
    def _make_request(self, service: str, action: str, *,  # pylint: disable=too-many-arguments
                     params: Optional[Dict[str, Any]] = None,
                     use_json: bool = False,
                     path: Optional[str] = None,
                     body: Optional[str] = None,
                     signing_service: Optional[str] = None) -> str:
        """Make AWS API request with retry logic for network errors.
        Retries on transient network errors (DNS failures, timeouts) with
        exponential backoff. Does not retry on HTTP errors (auth, permissions, etc).
        Args:
            service: AWS service name for endpoint (e.g., 'bedrock-runtime')
            action: API action name
            params: API parameters dict
            use_json: Use JSON API format (for services like Secrets Manager)
            path: Custom URI path (for REST APIs like Bedrock)
            body: Custom request body (for REST APIs like Bedrock)
            signing_service: Override service name for signing (e.g., 'bedrock' for bedrock-runtime)
        """
        if service == 'iam':
            host = 'iam.amazonaws.com'
        else:
            host = f"{service}.{self.region}.amazonaws.com"
        for attempt in range(4):
            if path and body:
                req = self._prepare_rest_api_request_with_signing(
                    signing_service or service, host, path, body
                )
            elif use_json:
                req = self._prepare_json_api_request_with_signing(
                    signing_service or service, action, host, params
                )
            else:
                req = self._prepare_query_api_request_with_signing(
                    signing_service or service, action, host, params
                )
            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    return response.read().decode('utf-8')
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8') if e.fp else ''
                logging.error("AWS API error: %s %s", e.code, e.reason)
                if error_body:
                    logging.error("Error details: %s", error_body)
                raise AWSHTTPError(e, error_body) from e
            except urllib.error.URLError as e:
                if attempt == 3:
                    logging.error("Network error after 4 attempts: %s", e.reason)
                    raise
                delay = (2 ** attempt) + random.uniform(0, 1)
                logging.warning("Network error on attempt %d/4: %s - retrying in %.1fs...",
                              attempt + 1, e.reason, delay)
                time.sleep(delay)
        raise RuntimeError("Retry loop completed without returning")
class STSClient(AWSClientBase):
    def test_sts_access(self) -> None:
        self._make_request('sts', 'GetCallerIdentity', params={})
    def get_account_id(self) -> str:
        response = self._make_request('sts', 'GetCallerIdentity', params={})
        root = ET.fromstring(response)
        account_id_elem = root.find('.//{*}Account')
        return account_id_elem.text
    def assume_role_with_web_identity(self, role_arn: str, web_identity_token: str,
                                      role_session_name: str = 'bootstrap-session') -> Optional[Dict[str, str]]:
        """Assume IAM role using OIDC web identity token.
        Args:
            role_arn: ARN of the role to assume
            web_identity_token: OIDC token from GitHub Actions
            role_session_name: Name for the session
        Returns:
            Dictionary with temporary credentials (access_key_id, secret_access_key, session_token)
            or None if failed
        """
        try:
            response = self._make_request('sts', 'AssumeRoleWithWebIdentity', params={
                'RoleArn': role_arn,
                'RoleSessionName': role_session_name,
                'WebIdentityToken': web_identity_token
            })
            root = ET.fromstring(response)
            access_key = root.find('.//{*}AccessKeyId')
            secret_key = root.find('.//{*}SecretAccessKey')
            session_token = root.find('.//{*}SessionToken')
            if access_key is not None and secret_key is not None and session_token is not None:
                return {
                    'access_key_id': access_key.text,
                    'secret_access_key': secret_key.text,
                    'session_token': session_token.text
                }
            logging.error("Failed to parse credentials from AssumeRoleWithWebIdentity response")
            return None
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to assume role with web identity: %s", e)
            return None
        except ET.ParseError as e:
            logging.error("Failed to parse AssumeRoleWithWebIdentity XML response: %s", e)
            return None
class IAMClient(AWSClientBase):
    def oidc_provider_exists(self, account_id: str) -> bool:
        arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
        try:
            self._make_request('iam', 'GetOpenIDConnectProvider', params={
                'OpenIDConnectProviderArn': arn
            })
            return True
        except AWSHTTPError as e:
            if e.code == 404:
                return False
            raise
    def create_oidc_provider(self) -> bool:
        thumbprint = "6938fd4d98bab03faadb97b34396831e3780aea1"
        try:
            response = self._make_request('iam', 'CreateOpenIDConnectProvider', params={
                'Url': 'https://token.actions.githubusercontent.com',
                'ClientIDList.member.1': 'sts.amazonaws.com',
                'ThumbprintList.member.1': thumbprint,
                'Tags.member.1.Key': 'Name',
                'Tags.member.1.Value': 'GitHubActions'
            })
            logging.debug("OIDC provider created: %s", response)
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to create OIDC provider: %s", e)
            return False
    def role_exists(self, role_name: str) -> bool:
        try:
            self._make_request('iam', 'GetRole', params={
                'RoleName': role_name
            })
            return True
        except AWSHTTPError as e:
            if e.code == 404:
                return False
            raise
    def get_role_trust_policy(self, role_name: str) -> Optional[Dict[str, Any]]:
        try:
            response = self._make_request('iam', 'GetRole', params={
                'RoleName': role_name
            })
            root = ET.fromstring(response)
            policy_elem = root.find('.//{*}AssumeRolePolicyDocument')
            if policy_elem is not None and policy_elem.text:
                decoded_policy = unquote(policy_elem.text)
                return json.loads(decoded_policy)
            return None
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to get role trust policy: %s", e)
            return None
    def update_role_trust_policy(self, role_name: str, trust_policy: Dict[str, Any]) -> bool:
        try:
            self._make_request('iam', 'UpdateAssumeRolePolicy', params={
                'RoleName': role_name,
                'PolicyDocument': json.dumps(trust_policy)
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to update role trust policy: %s", e)
            return False
    def create_role(self, role_name: str, trust_policy: Dict[str, Any]) -> bool:
        try:
            response = self._make_request('iam', 'CreateRole', params={
                'RoleName': role_name,
                'AssumeRolePolicyDocument': json.dumps(trust_policy),
                'Description': 'Role for GitHub Actions workflows',
                'Tags.member.1.Key': 'ManagedBy',
                'Tags.member.1.Value': 'bootstrap-script'
            })
            logging.debug("Role created: %s", response)
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to create role: %s", e)
            return False
    def attach_managed_policy(self, role_name: str, policy_arn: str) -> bool:
        try:
            self._make_request('iam', 'AttachRolePolicy', params={
                'RoleName': role_name,
                'PolicyArn': policy_arn
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to attach policy: %s", e)
            return False
    def put_role_policy(self, role_name: str, policy_name: str,
                       policy_document: Dict[str, Any]) -> bool:
        """Put inline policy on role."""
        try:
            self._make_request('iam', 'PutRolePolicy', params={
                'RoleName': role_name,
                'PolicyName': policy_name,
                'PolicyDocument': json.dumps(policy_document)
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to put role policy: %s", e)
            return False
    def managed_policy_attached(self, role_name: str, policy_arn: str) -> bool:
        try:
            response = self._make_request('iam', 'ListAttachedRolePolicies', params={
                'RoleName': role_name
            })
            root = ET.fromstring(response)
            for member in root.findall('.//{*}member'):
                arn_elem = member.find('.//{*}PolicyArn')
                if arn_elem is not None and arn_elem.text == policy_arn:
                    return True
            return False
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to check policy attachment (network error): %s", e)
            return False
        except ET.ParseError as e:
            logging.error("Failed to parse policy attachment response: %s", e)
            return False
    def inline_policy_exists(self, role_name: str, policy_name: str) -> bool:
        try:
            self._make_request('iam', 'GetRolePolicy', params={
                'RoleName': role_name,
                'PolicyName': policy_name
            })
            return True
        except AWSHTTPError as e:
            if e.code == 404:
                return False
            raise
    def detach_managed_policy(self, role_name: str, policy_arn: str) -> bool:
        try:
            self._make_request('iam', 'DetachRolePolicy', params={
                'RoleName': role_name,
                'PolicyArn': policy_arn
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to detach policy: %s", e)
            return False
    def delete_role_policy(self, role_name: str, policy_name: str) -> bool:
        try:
            self._make_request('iam', 'DeleteRolePolicy', params={
                'RoleName': role_name,
                'PolicyName': policy_name
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to delete role policy: %s", e)
            return False
    def delete_role(self, role_name: str) -> bool:
        try:
            self._make_request('iam', 'DeleteRole', params={
                'RoleName': role_name
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to delete role: %s", e)
            return False
    def delete_oidc_provider(self, account_id: str) -> bool:
        arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
        try:
            self._make_request('iam', 'DeleteOpenIDConnectProvider', params={
                'OpenIDConnectProviderArn': arn
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to delete OIDC provider: %s", e)
            return False
    def test_iam_access(self) -> None:
        self._make_request('iam', 'ListRoles', params={'MaxItems': 1})
class SecretsManagerClient(AWSClientBase):
    def create_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        try:
            self._make_request('secretsmanager', 'CreateSecret', params={
                'Name': secret_name,
                'Description': 'GitHub runner credentials',
                'SecretString': json.dumps(secret_value),
                'ClientRequestToken': str(uuid.uuid4())
            }, use_json=True)
            return True
        except AWSHTTPError as e:
            if 'ResourceExistsException' in e.error_body:
                logging.info("Secret already exists, updating instead")
                return self.update_secret(secret_name, secret_value)
            raise
    def update_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        try:
            self._make_request('secretsmanager', 'PutSecretValue', params={
                'SecretId': secret_name,
                'SecretString': json.dumps(secret_value),
                'ClientRequestToken': str(uuid.uuid4())
            }, use_json=True)
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to update secret: %s", e)
            return False
    def secret_exists(self, secret_name: str) -> bool:
        try:
            self._make_request('secretsmanager', 'DescribeSecret', params={
                'SecretId': secret_name
            }, use_json=True)
            return True
        except AWSHTTPError as e:
            if e.code == 400:
                return False
            raise
    def get_secret_value(self, secret_name: str) -> Optional[Dict[str, Any]]:
        try:
            response_bytes = self._make_request('secretsmanager', 'GetSecretValue', params={
                'SecretId': secret_name
            }, use_json=True)
            response_data = json.loads(response_bytes)
            secret_string = response_data.get('SecretString')
            if secret_string:
                return json.loads(secret_string)
            logging.error("Secret %s has no SecretString field", secret_name)
            return None
        except AWSHTTPError as e:
            if e.code == 400:
                logging.error("Secret %s not found", secret_name)
            else:
                logging.error("Failed to retrieve secret %s: HTTP %d", secret_name, e.code)
            return None
        except json.JSONDecodeError as e:
            logging.error("Failed to parse secret %s value: %s", secret_name, e)
            return None
    def delete_secret(self, secret_name: str) -> bool:
        try:
            self._make_request('secretsmanager', 'DeleteSecret', params={
                'SecretId': secret_name,
                'ForceDeleteWithoutRecovery': True
            }, use_json=True)
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to delete secret: %s", e)
            return False
    def test_secrets_manager_access(self) -> None:
        self._make_request('secretsmanager', 'ListSecrets', params={'MaxResults': 1}, use_json=True)
class BedrockClient(AWSClientBase):
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, region: str, access_key_id: str, secret_access_key: str,
                 session_token: Optional[str] = None, model_id: str = 'amazon.nova-micro-v1:0'):
        super().__init__(region, access_key_id, secret_access_key, session_token)
        self.model_id = model_id
    def invoke_model(self, prompt: str, max_tokens: int = 16000) -> str:
        # Cap max_tokens based on model limits
        # Amazon Nova models: 10240 max
        # Anthropic Claude: 16000+ supported
        if not self.model_id.startswith('anthropic'):
            max_tokens = min(max_tokens, 10240)

        # Amazon Nova uses a different request format than Anthropic Claude
        if self.model_id.startswith('anthropic'):
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]
            })
        else:  # Amazon Nova and other models
            body = json.dumps({
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {"max_new_tokens": max_tokens}
            })
        response = self._make_request(
            'bedrock-runtime',
            'InvokeModel',
            path=f"/model/{self.model_id}/invoke",
            body=body,
            use_json=True,
            signing_service='bedrock'
        )
        result = json.loads(response)
        # Parse response based on model type
        if self.model_id.startswith('anthropic'):
            return result['content'][0]['text']
        # Amazon Nova
        return result['output']['message']['content'][0]['text']
    def _is_already_exists_error(self, error: AWSHTTPError) -> bool:
        """Check if error indicates resource already exists."""
        return 'AlreadyExists' in error.error_body or 'already' in error.error_body.lower()
    def enable_model_access(self) -> bool:
        # Amazon Nova and other models are available by default, only Anthropic models require this process
        if not self.model_id.startswith('anthropic'):
            logging.info("Model %s is available by default, skipping access setup", self.model_id)
            return True

        logging.info("Enabling Anthropic model access for %s (one-time setup)...", self.model_id)
        if not self._submit_use_case():
            return False
        self._accept_model_agreement()
        return self._request_model_entitlement()
    def _submit_use_case(self) -> bool:
        """Submit use case form for Bedrock model access."""
        try:
            form_data = {
                "companyName": "GitHub Actions Automation",
                "companyWebsite": "https://github.com",
                "intendedUsers": "0",
                "industryOption": "Technology",
                "useCases": "Automated documentation generation and code review"
            }
            self._make_request(
                'bedrock',
                'PutUseCaseForModelAccess',
                path='/put-use-case-for-model-access',
                body=json.dumps({'formData': json.dumps(form_data)})
            )
            logging.info("✓ Submitted use case form")
            return True
        except AWSHTTPError as e:
            if self._is_already_exists_error(e):
                logging.info("Use case already submitted, continuing...")
                return True
            logging.error("Failed to submit use case: %s", e)
            return False
    def _accept_model_agreement(self) -> None:
        """Accept model agreement if offers are available."""
        try:
            response = self._make_request(
                'bedrock',
                'ListFoundationModelAgreementOffers',
                path='/list-foundation-model-agreement-offers',
                body=json.dumps({'modelId': self.model_id})
            )
            offers = json.loads(response).get('offers', [])
            if not offers:
                logging.info("No agreement offers (may already be accepted)")
                return
            offer_token = offers[0]['offerToken']
            self._make_request(
                'bedrock',
                'CreateFoundationModelAgreement',
                path='/create-foundation-model-agreement',
                body=json.dumps({'modelId': self.model_id, 'offerToken': offer_token})
            )
            logging.info("✓ Accepted model agreement for %s", self.model_id)
        except AWSHTTPError as e:
            if self._is_already_exists_error(e):
                logging.info("Agreement already accepted, continuing...")
            else:
                logging.warning("Failed to create agreement: %s", e)
    def _request_model_entitlement(self) -> bool:
        """Request model entitlement."""
        try:
            self._make_request(
                'bedrock',
                'FoundationModelEntitlement',
                path='/foundation-model-entitlement',
                body=json.dumps({'modelId': self.model_id})
            )
            logging.info("✓ Requested model entitlement for %s", self.model_id)
            logging.info("✓ Anthropic model access enabled for %s", self.model_id)
            return True
        except AWSHTTPError as e:
            if self._is_already_exists_error(e):
                logging.info("Entitlement already exists, continuing...")
                logging.info("✓ Anthropic model access enabled for %s", self.model_id)
                return True
            if 'not authorized to perform this action' in e.error_body:
                logging.error("FATAL: AWS account not authorized for Bedrock model access")
                logging.error("ACTION REQUIRED: Create AWS support case to enable Bedrock")
                logging.error("Visit: https://console.aws.amazon.com/support/home")
                logging.error("Describe your use case for Bedrock model access")
                return False
            logging.error("Failed to request model entitlement: %s", e)
            return False
class AWSClientStdlib:
    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, region: str, access_key_id: str, secret_access_key: str,
                 session_token: Optional[str] = None, bedrock_model_id: str = 'amazon.nova-micro-v1:0'):
        """Initialize AWS service clients."""
        self.sts = STSClient(region, access_key_id, secret_access_key, session_token)
        self.iam = IAMClient(region, access_key_id, secret_access_key, session_token)
        self.secrets = SecretsManagerClient(region, access_key_id, secret_access_key, session_token)
        self.bedrock = BedrockClient(region, access_key_id, secret_access_key, session_token, bedrock_model_id)
        self.region = region
    def get_account_id(self) -> str:
        return self.sts.get_account_id()
    def validate_access(self) -> None:
        try:
            self.sts.test_sts_access()
        except AWSHTTPError as e:
            logging.error("STS access denied: %s", e.reason)
            raise
        try:
            self.iam.test_iam_access()
        except AWSHTTPError as e:
            logging.error("IAM access denied: %s", e.reason)
            raise
        try:
            self.secrets.test_secrets_manager_access()
        except AWSHTTPError as e:
            logging.error("Secrets Manager access denied: %s", e.reason)
            raise
def normalize_policy(policy: Dict[str, Any]) -> str:
    return json.dumps(policy, sort_keys=True, separators=(',', ':'))
def policies_equal(policy1: Dict[str, Any], policy2: Dict[str, Any]) -> bool:
    return normalize_policy(policy1) == normalize_policy(policy2)
def create_trust_policy(account_id: str, github_org: str, github_repo: str) -> Dict[str, Any]:
    return {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Federated": f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": f"repo:{github_org}/{github_repo}:*"
                }
            }
        }]
    }
def create_iam_role_management_policy() -> Dict[str, Any]:
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "iam:CreateRole",
                    "iam:DeleteRole",
                    "iam:GetRole",
                    "iam:UpdateRole",
                    "iam:UpdateAssumeRolePolicy",
                    "iam:AttachRolePolicy",
                    "iam:DetachRolePolicy",
                    "iam:PutRolePolicy",
                    "iam:DeleteRolePolicy",
                    "iam:GetRolePolicy",
                    "iam:ListAttachedRolePolicies",
                    "iam:ListRolePolicies",
                    "iam:CreateInstanceProfile",
                    "iam:DeleteInstanceProfile",
                    "iam:GetInstanceProfile",
                    "iam:AddRoleToInstanceProfile",
                    "iam:RemoveRoleFromInstanceProfile",
                    "iam:PassRole",
                    "iam:TagRole",
                    "iam:UntagRole",
                    "iam:CreateOpenIDConnectProvider",
                    "iam:DeleteOpenIDConnectProvider",
                    "iam:GetOpenIDConnectProvider",
                    "iam:TagOpenIDConnectProvider",
                    "iam:UntagOpenIDConnectProvider"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:ListFoundationModels",
                    "bedrock:PutUseCaseForModelAccess",
                    "bedrock:ListFoundationModelAgreementOffers",
                    "bedrock:CreateFoundationModelAgreement"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel"
                ],
                "Resource": [
                    "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0",
                    "arn:aws:bedrock:us-east-1::foundation-model/openai.gpt-oss-120b-1:0"
                ]
            }
        ]
    }
def create_secret_value(github_token: str, github_org: str, github_repo: str) -> Dict[str, Any]:
    return {
        "auth_method": "classic-pat",
        "github_token": github_token,
        "github_org": github_org,
        "github_repo": github_repo,
        "created_by": "bootstrap-script",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
def _setup_authentication_for_create(args: argparse.Namespace, state: str, is_workflow: bool):
    if state == 'warm' and is_workflow:
        logging.info("Using OIDC authentication (warm state)")
        oidc_creds = assume_role_with_oidc(args.aws_account_id, args.aws_region, args.aws_iam_role_name)
        if not oidc_creds:
            logging.error("Failed to assume role with OIDC - falling back to direct credentials")
            aws_access_key = args.aws_access_key_id
            aws_secret_key = args.aws_secret_access_key
            session_token = None
        else:
            aws_access_key = oidc_creds['access_key_id']
            aws_secret_key = oidc_creds['secret_access_key']
            session_token = oidc_creds['session_token']
        secret_data = get_secret_from_secrets_manager(
            args.github_pat_secret_name,
            args.aws_region,
            aws_access_key,
            aws_secret_key,
            session_token
        )
        if secret_data:
            github_token = secret_data.get('github_token')
            logging.info("Retrieved GitHub PAT from Secrets Manager")
        else:
            logging.warning("Could not retrieve GitHub PAT from Secrets Manager - using provided token")
            github_token = args.github_token
    else:
        logging.info("Using direct credentials (cold start)")
        aws_access_key = args.aws_access_key_id
        aws_secret_key = args.aws_secret_access_key
        github_token = args.github_token
        session_token = None
    return aws_access_key, aws_secret_key, session_token, github_token
def _create_oidc_provider_step(aws: AWSClientStdlib, account_id: str) -> int:
    logging.info("Checking if GitHub Actions OIDC provider exists")
    if aws.iam.oidc_provider_exists(account_id):
        logging.info("OIDC provider already exists, skipping creation")
        return 0
    logging.info("Creating GitHub Actions OIDC provider")
    if aws.iam.create_oidc_provider():
        logging.info("Created OIDC provider")
        return 0
    logging.error("Failed to create OIDC provider")
    return 1
def _create_iam_role_step(aws: AWSClientStdlib, args: argparse.Namespace,
                          trust_policy: Dict[str, Any]) -> int:
    """Create or update IAM role. Returns 0 on success, 1 on failure."""
    logging.info("Checking if IAM role '%s' exists", args.aws_iam_role_name)
    if aws.iam.role_exists(args.aws_iam_role_name):
        logging.info("IAM role already exists, checking trust policy")
        current_trust_policy = aws.iam.get_role_trust_policy(args.aws_iam_role_name)
        if current_trust_policy and not policies_equal(current_trust_policy, trust_policy):
            logging.info("Trust policy differs, updating")
            if not aws.iam.update_role_trust_policy(args.aws_iam_role_name, trust_policy):
                logging.error("Failed to update trust policy")
                return 1
            logging.info("Updated trust policy")
        else:
            logging.info("Trust policy up to date")
        return 0
    logging.info("Creating IAM role '%s'", args.aws_iam_role_name)
    if not aws.iam.create_role(args.aws_iam_role_name, trust_policy):
        logging.error("Failed to create IAM role")
        return 1
    logging.info("Created IAM role")
    return 0
def _attach_iam_policies_step(aws: AWSClientStdlib, role_name: str) -> int:
    logging.info("Checking if PowerUserAccess policy is attached")
    power_user_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
    if aws.iam.managed_policy_attached(role_name, power_user_arn):
        logging.info("PowerUserAccess policy already attached")
    else:
        logging.info("Attaching PowerUserAccess policy")
        if not aws.iam.attach_managed_policy(role_name, power_user_arn):
            logging.error("Failed to attach PowerUserAccess policy")
            return 1
        logging.info("Attached PowerUserAccess policy")
    logging.info("Updating IAM role management policy")
    policy = create_iam_role_management_policy()
    if not aws.iam.put_role_policy(role_name, "IAMRoleManagement", policy):
        logging.error("Failed to update IAM role management policy")
        return 1
    logging.info("Updated IAM role management policy")
    return 0
def _enable_bedrock_access_step(aws: AWSClientStdlib, enable: bool) -> int:
    if not enable:
        logging.info("Bedrock model access disabled (skipping)")
        return 0
    print()
    logging.info("Enabling Bedrock model access")
    if not aws.bedrock.enable_model_access():
        logging.error("Failed to enable Bedrock model access")
        return 1
    return 0
def _store_secret_and_cleanup_step(aws: AWSClientStdlib, args: argparse.Namespace,
                                    github_token: str, is_workflow: bool) -> int:
    """Store GitHub PAT and cleanup GitHub Secrets. Returns 0 on success, 1 on failure."""
    print()
    logging.info("Storing GitHub PAT in AWS Secrets Manager")
    secret_value = create_secret_value(github_token, args.github_org, args.github_repo)
    if not aws.secrets.create_secret(args.github_pat_secret_name, secret_value):
        logging.error("Failed to store credentials in Secrets Manager")
        return 1
    logging.info("Stored credentials in Secrets Manager")
    print()
    print("Bootstrap complete")
    print("OIDC provider created")
    print(f"IAM role created: {args.aws_iam_role_name}")
    print("GitHub PAT stored in Secrets Manager")
    if is_workflow:
        print()
        logging.info("Transitioning to pure OIDC automation...")
        logging.info("Deleting human credentials from GitHub Secrets")
        secrets_to_delete = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'GH_RUNNER_PAT'
        ]
        success = delete_github_secrets(
            github_token,
            args.github_org,
            args.github_repo,
            secrets_to_delete
        )
        if success:
            print()
            print("AUTOMATION TO THE MOON!")
            print("Human credentials deleted - system now runs on PURE OIDC!")
        else:
            logging.warning("Some credentials could not be deleted")
    print()
    return 0
def create_resources(args: argparse.Namespace) -> int:
    is_workflow = is_running_in_github_actions()
    state = detect_bootstrap_state(
        args.aws_account_id,
        args.aws_region,
        args.aws_iam_role_name,
        args.aws_access_key_id,
        args.aws_secret_access_key
    )
    aws_access_key, aws_secret_key, session_token, github_token = _setup_authentication_for_create(
        args, state, is_workflow
    )
    aws = AWSClientStdlib(
        args.aws_region,
        access_key_id=aws_access_key,
        secret_access_key=aws_secret_key,
        session_token=session_token,
        bedrock_model_id=args.bedrock_model_id
    )
    print()
    print("GitHub Actions Self-Hosted Runners Bootstrap")
    print("=" * 50)
    print()
    print("Configuration:")
    print(f"  AWS Account: {args.aws_account_id}")
    print(f"  AWS Region:  {args.aws_region}")
    print(f"  GitHub Org:  {args.github_org}")
    print(f"  GitHub Repo: {args.github_repo}")
    print(f"  IAM Role:    {args.aws_iam_role_name}")
    print(f"  State:       {state.upper()}")
    print(f"  Mode:        {'Workflow' if is_workflow else 'Local'}")
    print("  AWS Client:  Pure Python stdlib (self-contained)")
    print(f"  Auth:        {'OIDC' if state == 'warm' and is_workflow else 'Direct credentials'}")
    print()
    print()
    validate_aws_credentials(aws)
    validate_github_pat(github_token)
    print()
    if _create_oidc_provider_step(aws, args.aws_account_id) != 0:
        return 1
    trust_policy = create_trust_policy(args.aws_account_id, args.github_org, args.github_repo)
    if _create_iam_role_step(aws, args, trust_policy) != 0:
        return 1
    if _attach_iam_policies_step(aws, args.aws_iam_role_name) != 0:
        return 1
    if _enable_bedrock_access_step(aws, args.enable_bedrock) != 0:
        return 1
    print()
    validate_oidc_role_permissions(aws, args.aws_iam_role_name)
    print()
    return _store_secret_and_cleanup_step(aws, args, github_token, is_workflow)
def _setup_authentication_for_destroy(args: argparse.Namespace, state: str, is_workflow: bool):
    if state == 'warm' and is_workflow:
        logging.info("Using OIDC authentication for destruction (warm state)")
        oidc_creds = assume_role_with_oidc(args.aws_account_id, args.aws_region, args.aws_iam_role_name)
        if not oidc_creds:
            logging.error("Failed to assume role with OIDC - falling back to direct credentials")
            return args.aws_access_key_id, args.aws_secret_access_key, None
        return oidc_creds['access_key_id'], oidc_creds['secret_access_key'], oidc_creds['session_token']
    logging.info("Using direct credentials for destruction")
    return args.aws_access_key_id, args.aws_secret_access_key, None
def _delete_secret_step(aws: AWSClientStdlib, secret_name: str) -> int:
    logging.info("Checking if GitHub PAT secret exists")
    if not aws.secrets.secret_exists(secret_name):
        logging.info("Secret does not exist, skipping deletion")
        return 0
    logging.info("Deleting GitHub PAT from Secrets Manager")
    if not aws.secrets.delete_secret(secret_name):
        logging.error("Failed to delete secret")
        return 1
    logging.info("Deleted secret")
    return 0
def _delete_iam_role_step(aws: AWSClientStdlib, role_name: str) -> int:
    logging.info("Checking if IAM role '%s' exists", role_name)
    if not aws.iam.role_exists(role_name):
        logging.info("IAM role does not exist, skipping deletion")
        return 0
    logging.info("Detaching PowerUserAccess policy")
    power_user_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
    if not aws.iam.detach_managed_policy(role_name, power_user_arn):
        logging.error("Failed to detach PowerUserAccess policy")
        return 1
    logging.info("Detached PowerUserAccess policy")
    logging.info("Deleting IAM role management policy")
    if not aws.iam.delete_role_policy(role_name, "IAMRoleManagement"):
        logging.error("Failed to delete IAM role management policy")
        return 1
    logging.info("Deleted IAM role management policy")
    logging.info("Deleting IAM role '%s'", role_name)
    if not aws.iam.delete_role(role_name):
        logging.error("Failed to delete IAM role")
        return 1
    logging.info("Deleted IAM role")
    return 0
def _delete_oidc_provider_step(aws: AWSClientStdlib, account_id: str) -> int:
    logging.info("Checking if GitHub Actions OIDC provider exists")
    if not aws.iam.oidc_provider_exists(account_id):
        logging.info("OIDC provider does not exist, skipping deletion")
        return 0
    logging.info("Deleting GitHub Actions OIDC provider")
    if not aws.iam.delete_oidc_provider(account_id):
        logging.error("Failed to delete OIDC provider")
        return 1
    logging.info("Deleted OIDC provider")
    return 0
def destroy_resources(args: argparse.Namespace) -> int:
    is_workflow = is_running_in_github_actions()
    state = detect_bootstrap_state(
        args.aws_account_id,
        args.aws_region,
        args.aws_iam_role_name,
        args.aws_access_key_id,
        args.aws_secret_access_key
    )
    aws_access_key, aws_secret_key, session_token = _setup_authentication_for_destroy(args, state, is_workflow)
    if not aws_access_key or not aws_secret_key:
        logging.error("Missing required credentials")
        return 1
    aws = AWSClientStdlib(
        args.aws_region,
        access_key_id=aws_access_key,
        secret_access_key=aws_secret_key,
        session_token=session_token,
        bedrock_model_id='amazon.nova-micro-v1:0'  # Default for destroy, not used
    )
    if not args.force:
        try:
            confirm = input("Are you sure you want to destroy all bootstrap resources? ([y]/n): ").strip().lower() or 'y'
            abort = confirm not in ('y', 'yes')
        except KeyboardInterrupt:
            abort = True
            print()
        if abort:
            print("Aborted")
            return 1
    if _delete_secret_step(aws, args.github_pat_secret_name) != 0:
        return 1
    if _delete_iam_role_step(aws, args.aws_iam_role_name) != 0:
        return 1
    if _delete_oidc_provider_step(aws, args.aws_account_id) != 0:
        return 1
    print()
    print("All bootstrap resources destroyed")
    print()
    return 0
def validate_aws_credentials(aws_client: 'AWSClientStdlib') -> None:
    logging.info("Validating AWS credentials...")
    try:
        aws_client.validate_access()
        logging.info("✓ AWS credentials validated")
    except AWSHTTPError as e:
        logging.error("FATAL: %s", e.reason)
        if "STS" in e.reason:
            logging.error("Check that AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are correct")
        elif "IAM" in e.reason:
            logging.error("Required: IAM read/write permissions (PowerUserAccess + IAM or AdministratorAccess)")
        elif "Secrets Manager" in e.reason:
            logging.error("Required: Secrets Manager read/write permissions")
        sys.exit(1)
def validate_github_pat(github_token: str) -> None:
    logging.info("Validating GitHub PAT...")
    try:
        req = urllib.request.Request(
            'https://api.github.com/user',
            method='HEAD',
            headers={
                'Authorization': f'Bearer {github_token}',
                'Accept': 'application/vnd.github+json',
                'X-GitHub-Api-Version': '2022-11-28'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            scopes_header = response.headers.get('X-OAuth-Scopes', '')
            scopes_list = [s.strip() for s in scopes_header.split(',') if s.strip()]
            logging.info("GitHub PAT scopes: %s", ', '.join(scopes_list))
            missing_scopes = []
            if 'admin:org' not in scopes_list:
                missing_scopes.append('admin:org')
            if 'repo' not in scopes_list:
                missing_scopes.append('repo')
            if missing_scopes:
                logging.error("FATAL: GitHub PAT missing required scopes: %s", ', '.join(missing_scopes))
                logging.error("Required scopes:")
                logging.error("  - admin:org (for runner registration)")
                logging.error("  - repo (for managing repository secrets)")
                logging.error("Create a new PAT at: https://github.com/settings/tokens/new?scopes=admin:org,repo")
                sys.exit(1)
            logging.info("✓ GitHub PAT validated")
    except AWSHTTPError as e:
        if e.code == 401:
            logging.error("FATAL: GitHub PAT is invalid or expired")
        else:
            logging.error("FATAL: Cannot validate GitHub PAT (HTTP %s): %s", e.code, e.reason)
        sys.exit(1)
    except urllib.error.URLError as e:
        logging.error("FATAL: Network error validating GitHub PAT: %s", e)
        sys.exit(1)
    except (json.JSONDecodeError, KeyError) as e:
        logging.error("FATAL: Invalid GitHub API response: %s", e)
        sys.exit(1)
def validate_oidc_role_permissions(aws_client: 'AWSClientStdlib',
                                   role_name: str) -> None:
    """Validate OIDC IAM role has required permissions.
    Checks that role has:
    - PowerUserAccess managed policy attached
    - IAMRoleManagement inline policy attached
    Exits with code 1 if validation fails (FATAL).
    """
    logging.info("Validating OIDC role permissions...")
    power_user_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
    if not aws_client.iam.managed_policy_attached(role_name, power_user_arn):
        logging.error("FATAL: OIDC role '%s' missing PowerUserAccess managed policy", role_name)
        sys.exit(1)
    logging.info("✓ PowerUserAccess policy attached")
    if not aws_client.iam.inline_policy_exists(role_name, 'IAMRoleManagement'):
        logging.error("FATAL: OIDC role '%s' missing IAMRoleManagement inline policy", role_name)
        sys.exit(1)
    logging.info("✓ IAMRoleManagement policy attached")
    logging.info("✓ OIDC role permissions validated")
def delete_github_secrets(github_token: str, github_org: str, github_repo: str,
                          secret_names: list) -> bool:
    """Delete secrets from GitHub repository.
    Args:
        github_token: GitHub Personal Access Token with admin:org scope
        github_org: GitHub organization name
        github_repo: GitHub repository name
        secret_names: List of secret names to delete
    Returns:
        True if all secrets deleted successfully (or already deleted), False otherwise
    """
    logging.info("Deleting human credentials from GitHub Secrets (AUTOMATION TO THE MOON!)")
    all_success = True
    for secret_name in secret_names:
        logging.info("Deleting %s...", secret_name)
        url = f"https://api.github.com/repos/{github_org}/{github_repo}/actions/secrets/{secret_name}"
        try:
            req = urllib.request.Request(
                url,
                method='DELETE',
                headers={
                    'Accept': 'application/vnd.github+json',
                    'Authorization': f'Bearer {github_token}',
                    'X-GitHub-Api-Version': '2022-11-28'
                }
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 204:
                    logging.info("Deleted %s", secret_name)
                else:
                    logging.warning("Unexpected status code %s for %s", response.status, secret_name)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logging.info("%s already deleted", secret_name)
            else:
                logging.error("Failed to delete %s (HTTP %s)", secret_name, e.code)
                all_success = False
        except urllib.error.URLError as e:
            logging.error("Failed to delete %s (network error): %s", secret_name, e)
            all_success = False
    if all_success:
        logging.info("All human credentials deleted - system now runs on PURE OIDC!")
    return all_success
def _get_credentials_for_state(args: argparse.Namespace) -> tuple:
    is_workflow = is_running_in_github_actions()
    state = detect_bootstrap_state(
        args.aws_account_id,
        args.aws_region,
        args.aws_iam_role_name,
        args.aws_access_key_id if hasattr(args, 'aws_access_key_id') else None,
        args.aws_secret_access_key if hasattr(args, 'aws_secret_access_key') else None
    )
    if state == 'warm' and is_workflow:
        logging.info("Using OIDC authentication (warm state)")
        oidc_creds = assume_role_with_oidc(args.aws_account_id, args.aws_region, args.aws_iam_role_name)
        if not oidc_creds:
            logging.error("Failed to assume role with OIDC")
            return None, None, None
        return oidc_creds['access_key_id'], oidc_creds['secret_access_key'], oidc_creds['session_token']
    if hasattr(args, 'aws_access_key_id') and hasattr(args, 'aws_secret_access_key'):
        logging.info("Using direct credentials")
        return args.aws_access_key_id, args.aws_secret_access_key, None
    logging.error("No credentials available")
    return None, None, None
def _check_readme_needs_update(bedrock: BedrockClient, bootstrap_code: str, current_readme: str) -> bool:
    # If README doesn't exist or is empty, it definitely needs to be created
    if not current_readme or not current_readme.strip():
        return True
    prompt = f"""You are a technical documentation expert. Your task is to determine if a README file needs to be updated based on changes in the source code.
Here is the current Python source code:
<source_code>
{bootstrap_code}
</source_code>
Here is the current README:
<current_readme>
{current_readme}
</current_readme>
Analyze whether the README accurately reflects the current functionality, usage, and architecture described in the source code.
Does the README need updating? Respond with ONLY "true" or "false"."""
    response = bedrock.invoke_model(prompt, max_tokens=10)
    return response.strip().lower() == 'true'
def _update_readme(bedrock: BedrockClient, bootstrap_code: str) -> str:
    prompt = f"""You are a technical documentation expert. Generate a comprehensive README.md file for the following Python bootstrap script.
<source_code>
{bootstrap_code}
</source_code>

CRITICAL REQUIREMENTS TO EMPHASIZE:
- This script is SELF-CONTAINED and uses ONLY Python standard library (stdlib)
- NO external dependencies required (no pip install, no requirements.txt)
- NO AWS CLI required - implements AWS API calls using pure Python stdlib
- NO boto3 or other AWS SDKs - custom AWS client implementation using urllib and stdlib only
- This is a key selling point and architectural decision - must be prominently featured

Create a professional README that includes:
1. Title and brief overview emphasizing the self-contained, dependency-free nature
2. Purpose and what the script does
3. Requirements: ONLY Python 3.11+ (no other dependencies, explicitly state NO AWS CLI needed)
4. Usage instructions with command examples
5. Architecture overview (three-state system: COLD/WARM/DESTROY)
6. Configuration details
7. Authentication methods (OIDC vs direct credentials)
8. Implementation details: Pure Python stdlib implementation - custom AWS API clients without boto3
9. Security considerations
10. Troubleshooting tips

Format the README in clean, professional markdown. Be comprehensive but concise. Use code blocks for examples.
Generate ONLY the README content, starting with the title. Do not include any preamble or explanation."""
    try:
        return bedrock.invoke_model(prompt, max_tokens=16000)
    except Exception as e:
        logging.error("Failed to generate README via Bedrock: %s", e)
        raise
def cmd_readme(args: argparse.Namespace) -> int:  # pylint: disable=too-many-return-statements
    access_key, secret_key, session_token = _get_credentials_for_state(args)
    if not access_key:
        logging.error("Failed to obtain AWS credentials")
        return 1
    bedrock = BedrockClient(args.aws_region, access_key, secret_key, session_token)
    script_path = os.path.abspath(__file__)
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            bootstrap_code = f.read()
    except IOError as e:
        logging.error("Failed to read bootstrap.py: %s", e)
        return 1
    readme_path = os.path.join(os.path.dirname(script_path), 'README.md')
    current_readme = ""
    if os.path.exists(readme_path):
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                current_readme = f.read()
        except IOError as e:
            logging.error("Failed to read README.md: %s", e)
            return 1
    if args.check:
        logging.info("Checking if README needs update via Bedrock...")
        needs_update = _check_readme_needs_update(bedrock, bootstrap_code, current_readme)
        logging.info("README needs update" if needs_update else "README is current")
        print(needs_update)
        if args.output_file:
            with open(args.output_file, 'a', encoding='utf-8') as f:
                should_update = 'true' if needs_update else 'false'
                f.write(f'should_update={should_update}\n')
        return 0
    if args.update:
        logging.info("Generating updated README via Bedrock...")
        try:
            new_readme = _update_readme(bedrock, bootstrap_code)
        except (AWSHTTPError, urllib.error.URLError, urllib.error.HTTPError) as e:
            logging.error("Failed to generate README: %s", e)
            return 1
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(new_readme)
            logging.info("Updated README written to %s", readme_path)
            print(f"README updated successfully: {readme_path}")
            return 0
        except IOError as e:
            logging.error("Failed to write README: %s", e)
            return 1
    logging.error("Either --check or --update must be specified")
    return 1
def main():  # pylint: disable=too-many-return-statements,too-many-statements
    parser = argparse.ArgumentParser(
        description='Bootstrap AWS infrastructure for GitHub Actions self-hosted runners'
    )
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output (DEBUG level)')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Quiet mode, only show errors')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    create_parser = subparsers.add_parser('create', help='Create bootstrap resources')
    create_required = create_parser.add_argument_group('required arguments')
    create_required.add_argument('--aws-access-key-id', required=True,
                                help='AWS access key ID')
    create_required.add_argument('--aws-account-id', required=True,
                                help='AWS account ID (12 digits)')
    create_required.add_argument('--aws-iam-role-name', required=True,
                                help='IAM role name to create')
    create_required.add_argument('--aws-region', required=True,
                                help='AWS region (e.g., us-east-1)')
    create_required.add_argument('--aws-secret-access-key', required=True,
                                help='AWS secret access key')
    create_required.add_argument('--github-org', required=True,
                                help='GitHub organization name')
    create_required.add_argument('--github-repo', required=True,
                                help='GitHub repository name')
    create_required.add_argument('--github-token', required=True,
                                help='GitHub Classic PAT with admin:org scope')
    create_required.add_argument('--github-pat-secret-name', required=True,
                                help='AWS Secrets Manager secret name for GitHub PAT')
    create_optional = create_parser.add_argument_group('optional arguments')
    create_optional.add_argument('--bedrock-model-id', default='amazon.nova-micro-v1:0',
                                help='Bedrock model ID (default: amazon.nova-micro-v1:0)')
    create_optional.add_argument('--enable-bedrock', action='store_true', default=True,
                                help='Enable Bedrock model access (default: True)')
    destroy_parser = subparsers.add_parser('destroy', help='Destroy bootstrap resources')
    destroy_required = destroy_parser.add_argument_group('required arguments')
    destroy_required.add_argument('--aws-access-key-id', required=True,
                                 help='AWS access key ID')
    destroy_required.add_argument('--aws-account-id', required=True,
                                 help='AWS account ID (12 digits)')
    destroy_required.add_argument('--aws-iam-role-name', required=True,
                                 help='IAM role name to destroy')
    destroy_required.add_argument('--aws-region', required=True,
                                 help='AWS region (e.g., us-east-1)')
    destroy_required.add_argument('--aws-secret-access-key', required=True,
                                 help='AWS secret access key')
    destroy_required.add_argument('--github-org', required=True,
                                 help='GitHub organization name')
    destroy_required.add_argument('--github-repo', required=True,
                                 help='GitHub repository name')
    destroy_required.add_argument('--github-pat-secret-name', required=True,
                                 help='AWS Secrets Manager secret name for GitHub PAT')
    destroy_optional = destroy_parser.add_argument_group('optional arguments')
    destroy_optional.add_argument('--force', action='store_true',
                                 help='Skip confirmation prompt')
    readme_parser = subparsers.add_parser('readme', help='Check or update README via Bedrock')
    readme_required = readme_parser.add_argument_group('required arguments')
    readme_required.add_argument('--aws-account-id', required=True,
                                help='AWS account ID (12 digits)')
    readme_required.add_argument('--aws-iam-role-name', required=True,
                                help='IAM role name for OIDC authentication')
    readme_required.add_argument('--aws-region', required=True,
                                help='AWS region (e.g., us-east-1)')
    readme_action = readme_parser.add_mutually_exclusive_group(required=True)
    readme_action.add_argument('--check', action='store_true',
                              help='Check if README needs update (exits 0 if update needed)')
    readme_action.add_argument('--update', action='store_true',
                              help='Generate and write updated README')
    readme_parser.add_argument('--output-file',
                              help='Write result to file in key=value format (e.g., for CI/CD)')
    readme_optional = readme_parser.add_argument_group('optional arguments (for local execution)')
    readme_optional.add_argument('--aws-access-key-id',
                                help='AWS access key ID (not needed in GitHub Actions with OIDC)')
    readme_optional.add_argument('--aws-secret-access-key',
                                help='AWS secret access key (not needed in GitHub Actions with OIDC)')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    try:
        if args.command == 'create':
            return create_resources(args)
        if args.command == 'destroy':
            return destroy_resources(args)
        if args.command == 'readme':
            return cmd_readme(args)
        return 1
    except KeyboardInterrupt:
        print("\n\nAborted by user")
        return 130
    except (AWSHTTPError, urllib.error.URLError, urllib.error.HTTPError, IOError, OSError) as e:
        logging.error("Unexpected error: %s", e, exc_info=True)
        return 1
if __name__ == '__main__':
    sys.exit(main())
