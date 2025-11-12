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
def detect_infrastructure_state(account_id: str, region: str, role_name: str,
                                access_key_id: Optional[str] = None,
                                secret_access_key: Optional[str] = None) -> str:

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

    secrets_client = SecretsManagerClient(region, access_key_id, secret_access_key, session_token)
    return secrets_client.get_secret_value(secret_name)
class AWSClientBase:
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

        authorization_header = (
            f"AWS4-HMAC-SHA256 "
            f"Credential={self.access_key_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers_list}, "
            f"Signature={signature}"
        )
        return authorization_header
    def _sign_request(self, method: str, service: str, *,
                     request_data: Dict[str, Any]) -> Dict[str, str]:

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
    def _get_host(self, service: str) -> str:
        return 'iam.amazonaws.com' if service == 'iam' else f"{service}.{self.region}.amazonaws.com"

    def _retry_with_backoff(self, req: urllib.request.Request) -> str:
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=2 ** (attempt + 5)) as response:
                    return response.read().decode('utf-8')
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8') if e.fp else ''
                logging.error("AWS API error: %s %s", e.code, e.reason)
                if error_body:
                    logging.error("Error details: %s", error_body)
                raise AWSHTTPError(e, error_body) from e
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                if attempt == 3:
                    logging.error("Network/timeout error after 4 attempts: %s",
                                e.reason if hasattr(e, 'reason') else str(e))
                    raise
                delay = (2 ** attempt) + random.uniform(0, 1)
                logging.warning("Network/timeout error on attempt %d/4: %s - retrying in %.1fs (next timeout: %ds)...",
                              attempt + 1, e.reason if hasattr(e, 'reason') else str(e), delay, 2 ** (attempt + 6))
                time.sleep(delay)
        raise RuntimeError("Retry loop completed without returning")

    def make_request(self, service: str, action: str, *, params: Optional[Dict[str, Any]] = None) -> str:
        host = self._get_host(service)
        req = self._prepare_query_api_request_with_signing(service, action, host, params)
        return self._retry_with_backoff(req)

    def make_json_request(self, service: str, action: str, params: Optional[Dict[str, Any]]) -> str:
        host = self._get_host(service)
        req = self._prepare_json_api_request_with_signing(service, action, host, params)
        return self._retry_with_backoff(req)

    def make_rest_request(self, service: str, path: str, body: str, signing_service: str) -> str:
        host = self._get_host(service)
        req = self._prepare_rest_api_request_with_signing(signing_service, host, path, body)
        return self._retry_with_backoff(req)
class STSClient(AWSClientBase):
    def test_sts_access(self) -> None:
        self.make_request('sts', 'GetCallerIdentity', params={})
    def get_account_id(self) -> str:
        response = self.make_request('sts', 'GetCallerIdentity', params={})
        root = ET.fromstring(response)
        account_id_elem = root.find('.//{*}Account')
        if account_id_elem is None or account_id_elem.text is None:
            raise ValueError("Account ID not found in STS response")
        return account_id_elem.text
    def assume_role_with_web_identity(self, role_arn: str, web_identity_token: str,
                                      role_session_name: str = 'auth-session') -> Optional[Dict[str, str]]:

        try:
            response = self.make_request('sts', 'AssumeRoleWithWebIdentity', params={
                'RoleArn': role_arn,
                'RoleSessionName': role_session_name,
                'WebIdentityToken': web_identity_token
            })
            root = ET.fromstring(response)
            access_key = root.find('.//{*}AccessKeyId')
            secret_key = root.find('.//{*}SecretAccessKey')
            session_token = root.find('.//{*}SessionToken')


            if access_key is None or secret_key is None or session_token is None:
                logging.error("Failed to parse credentials from AssumeRoleWithWebIdentity response")
                return None


            if access_key.text is None or secret_key.text is None or session_token.text is None:
                logging.error("Failed to parse credentials from AssumeRoleWithWebIdentity response")
                return None

            return {
                'access_key_id': access_key.text,
                'secret_access_key': secret_key.text,
                'session_token': session_token.text
            }
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
            self.make_request('iam', 'GetOpenIDConnectProvider', params={
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
            response = self.make_request('iam', 'CreateOpenIDConnectProvider', params={
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
            self.make_request('iam', 'GetRole', params={
                'RoleName': role_name
            })
            return True
        except AWSHTTPError as e:
            if e.code == 404:
                return False
            raise
    def get_role_trust_policy(self, role_name: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.make_request('iam', 'GetRole', params={
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
            self.make_request('iam', 'UpdateAssumeRolePolicy', params={
                'RoleName': role_name,
                'PolicyDocument': json.dumps(trust_policy)
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to update role trust policy: %s", e)
            return False
    def create_role(self, role_name: str, trust_policy: Dict[str, Any]) -> bool:
        try:
            response = self.make_request('iam', 'CreateRole', params={
                'RoleName': role_name,
                'AssumeRolePolicyDocument': json.dumps(trust_policy),
                'Description': 'Role for GitHub Actions workflows',
                'Tags.member.1.Key': 'ManagedBy',
                'Tags.member.1.Value': 'auth-script'
            })
            logging.debug("Role created: %s", response)
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to create role: %s", e)
            return False
    def attach_managed_policy(self, role_name: str, policy_arn: str) -> bool:
        try:
            self.make_request('iam', 'AttachRolePolicy', params={
                'RoleName': role_name,
                'PolicyArn': policy_arn
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to attach policy: %s", e)
            return False
    def put_role_policy(self, role_name: str, policy_name: str,
                       policy_document: Dict[str, Any]) -> bool:

        try:
            self.make_request('iam', 'PutRolePolicy', params={
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
            response = self.make_request('iam', 'ListAttachedRolePolicies', params={
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
            self.make_request('iam', 'GetRolePolicy', params={
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
            self.make_request('iam', 'DetachRolePolicy', params={
                'RoleName': role_name,
                'PolicyArn': policy_arn
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to detach policy: %s", e)
            return False
    def delete_role_policy(self, role_name: str, policy_name: str) -> bool:
        try:
            self.make_request('iam', 'DeleteRolePolicy', params={
                'RoleName': role_name,
                'PolicyName': policy_name
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to delete role policy: %s", e)
            return False
    def list_attached_managed_policies(self, role_name: str) -> list:

        try:
            response = self.make_request('iam', 'ListAttachedRolePolicies', params={
                'RoleName': role_name
            })
            root = ET.fromstring(response)
            policy_arns = []
            for member in root.findall('.//{*}member'):
                arn_elem = member.find('.//{*}PolicyArn')
                if arn_elem is not None and arn_elem.text:
                    policy_arns.append(arn_elem.text)
            return policy_arns
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to list attached managed policies: %s", e)
            return []
        except ET.ParseError as e:
            logging.error("Failed to parse list attached policies response: %s", e)
            return []
    def list_inline_policies(self, role_name: str) -> list:

        try:
            response = self.make_request('iam', 'ListRolePolicies', params={
                'RoleName': role_name
            })
            root = ET.fromstring(response)
            policy_names = []
            for member in root.findall('.//{*}member'):
                if member.text:
                    policy_names.append(member.text)
            return policy_names
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to list inline policies: %s", e)
            return []
        except ET.ParseError as e:
            logging.error("Failed to parse list inline policies response: %s", e)
            return []
    def delete_role(self, role_name: str) -> bool:
        try:
            self.make_request('iam', 'DeleteRole', params={
                'RoleName': role_name
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to delete role: %s", e)
            return False
    def delete_oidc_provider(self, account_id: str) -> bool:
        arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
        try:
            self.make_request('iam', 'DeleteOpenIDConnectProvider', params={
                'OpenIDConnectProviderArn': arn
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to delete OIDC provider: %s", e)
            return False
    def test_iam_access(self) -> None:
        self.make_request('iam', 'ListRoles', params={'MaxItems': 1})
class SecretsManagerClient(AWSClientBase):
    def create_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        try:
            self.make_json_request('secretsmanager', 'CreateSecret', {
                'Name': secret_name,
                'Description': 'GitHub runner credentials',
                'SecretString': json.dumps(secret_value),
                'ClientRequestToken': str(uuid.uuid4())
            })
            return True
        except AWSHTTPError as e:
            if 'ResourceExistsException' in e.error_body:
                logging.info("Secret already exists, updating instead")
                return self.update_secret(secret_name, secret_value)
            raise
    def update_secret(self, secret_name: str, secret_value: Dict[str, Any]) -> bool:
        try:
            self.make_json_request('secretsmanager', 'PutSecretValue', {
                'SecretId': secret_name,
                'SecretString': json.dumps(secret_value),
                'ClientRequestToken': str(uuid.uuid4())
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to update secret: %s", e)
            return False
    def secret_exists(self, secret_name: str) -> bool:
        try:
            self.make_json_request('secretsmanager', 'DescribeSecret', {
                'SecretId': secret_name
            })
            return True
        except AWSHTTPError as e:
            if e.code == 400:
                return False
            raise
    def get_secret_value(self, secret_name: str) -> Optional[Dict[str, Any]]:
        try:
            response_bytes = self.make_json_request('secretsmanager', 'GetSecretValue', {
                'SecretId': secret_name
            })
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
            self.make_json_request('secretsmanager', 'DeleteSecret', {
                'SecretId': secret_name,
                'ForceDeleteWithoutRecovery': True
            })
            return True
        except (AWSHTTPError, urllib.error.URLError) as e:
            logging.error("Failed to delete secret: %s", e)
            return False
    def test_secrets_manager_access(self) -> None:
        self.make_json_request('secretsmanager', 'ListSecrets', {'MaxResults': 1})
class BedrockClient(AWSClientBase):
    def __init__(self, region: str, access_key_id: str, secret_access_key: str,
                 session_token: Optional[str] = None):
        super().__init__(region, access_key_id, secret_access_key, session_token)
        self.model_id = 'us.anthropic.claude-haiku-4-5-20251001-v1:0'
    def set_model_id(self, model_id: str):
        self.model_id = model_id
        return self
    def invoke_model(self, prompt: str, max_tokens: int = 16000) -> str:
        is_anthropic = (self.model_id.startswith('anthropic') or
                       self.model_id.startswith('us.anthropic') or
                       self.model_id.startswith('global.anthropic'))
        if not is_anthropic:
            max_tokens = min(max_tokens, 10240)

        if self.model_id.startswith('anthropic') or self.model_id.startswith('us.anthropic') or self.model_id.startswith('global.anthropic'):
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}]
            })
        else:
            body = json.dumps({
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {"max_new_tokens": max_tokens}
            })
        response = self.make_rest_request(
            'bedrock-runtime',
            f"/model/{self.model_id}/invoke",
            body,
            'bedrock'
        )
        result = json.loads(response)
        if is_anthropic:
            return result['content'][0]['text']
        return result['output']['message']['content'][0]['text']
    def _is_already_exists_error(self, error: AWSHTTPError) -> bool:

        return 'AlreadyExists' in error.error_body or 'already' in error.error_body.lower()
    def enable_model_access(self) -> bool:
        is_anthropic = (self.model_id.startswith('anthropic') or
                       self.model_id.startswith('us.anthropic') or
                       self.model_id.startswith('global.anthropic'))
        if not is_anthropic:
            logging.info("Model %s is available by default, skipping access setup", self.model_id)
            return True

        logging.info("Enabling Anthropic model access for %s (one-time setup)...", self.model_id)
        if not self._submit_use_case():
            return False
        self._accept_model_agreement()
        return self._request_model_entitlement()
    def _submit_use_case(self) -> bool:

        try:
            form_data = {
                "companyName": "GitHub Actions Automation",
                "companyWebsite": "https://github.com",
                "intendedUsers": "0",
                "industryOption": "Technology",
                "useCases": "Automated documentation generation and code review"
            }
            self.make_rest_request(
                'bedrock',
                '/put-use-case-for-model-access',
                json.dumps({'formData': json.dumps(form_data)}),
                'bedrock'
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

        try:
            response = self.make_rest_request(
                'bedrock',
                '/list-foundation-model-agreement-offers',
                json.dumps({'modelId': self.model_id}),
                'bedrock'
            )
            offers = json.loads(response).get('offers', [])
            if not offers:
                logging.info("No agreement offers (may already be accepted)")
                return
            offer_token = offers[0]['offerToken']
            self.make_rest_request(
                'bedrock',
                '/create-foundation-model-agreement',
                json.dumps({'modelId': self.model_id, 'offerToken': offer_token}),
                'bedrock'
            )
            logging.info("✓ Accepted model agreement for %s", self.model_id)
        except AWSHTTPError as e:
            if self._is_already_exists_error(e):
                logging.info("Agreement already accepted, continuing...")
            else:
                logging.warning("Failed to create agreement: %s", e)
    def _request_model_entitlement(self) -> bool:

        try:
            self.make_rest_request(
                'bedrock',
                '/foundation-model-entitlement',
                json.dumps({'modelId': self.model_id}),
                'bedrock'
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
    def __init__(self, region: str, access_key_id: str, secret_access_key: str,
                 session_token: Optional[str] = None):

        self.sts = STSClient(region, access_key_id, secret_access_key, session_token)
        self.iam = IAMClient(region, access_key_id, secret_access_key, session_token)
        self.secrets = SecretsManagerClient(region, access_key_id, secret_access_key, session_token)
        self.bedrock = BedrockClient(region, access_key_id, secret_access_key, session_token)
        self.region = region
    def set_bedrock_model_id(self, model_id: str):
        self.bedrock.set_model_id(model_id)
        return self
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
def create_secret_value(github_token: str, github_org: str, github_repo: str) -> Dict[str, Any]:
    return {
        "auth_method": "classic-pat",
        "github_token": github_token,
        "github_org": github_org,
        "github_repo": github_repo,
        "created_by": "auth-script",
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
    admin_arn = "arn:aws:iam::aws:policy/AdministratorAccess"


    attached_policies = aws.iam.list_attached_managed_policies(role_name)
    for policy_arn in attached_policies:
        if policy_arn != admin_arn:
            logging.info("Removing managed policy: %s", policy_arn)
            if not aws.iam.detach_managed_policy(role_name, policy_arn):
                logging.error("Failed to detach managed policy: %s", policy_arn)
                return 1
            logging.info("Removed managed policy: %s", policy_arn)


    inline_policies = aws.iam.list_inline_policies(role_name)
    for policy_name in inline_policies:
        logging.info("Removing inline policy: %s", policy_name)
        if not aws.iam.delete_role_policy(role_name, policy_name):
            logging.error("Failed to delete inline policy: %s", policy_name)
            return 1
        logging.info("Removed inline policy: %s", policy_name)


    if admin_arn not in attached_policies:
        logging.info("Attaching AdministratorAccess policy")
        if not aws.iam.attach_managed_policy(role_name, admin_arn):
            logging.error("Failed to attach AdministratorAccess policy")
            return 1
        logging.info("Attached AdministratorAccess policy")
    else:
        logging.info("AdministratorAccess policy already attached")

    return 0
def _store_secret_and_cleanup_step(aws: AWSClientStdlib, args: argparse.Namespace,
                                    github_token: str, is_workflow: bool) -> int:

    print()
    logging.info("Storing GitHub PAT in AWS Secrets Manager")
    secret_value = create_secret_value(github_token, args.github_org, args.github_repo)
    if not aws.secrets.create_secret(args.github_pat_secret_name, secret_value):
        logging.error("Failed to store credentials in Secrets Manager")
        return 1
    logging.info("Stored credentials in Secrets Manager")
    print()
    print("Infrastructure setup complete")
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
    state = detect_infrastructure_state(
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
        session_token=session_token
    ).set_bedrock_model_id(args.bedrock_model_id)
    print()
    print("AWS-GitHub Authentication Infrastructure")
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
    print()
    logging.info("Enabling Bedrock model access (auto-detects if needed)")
    if not aws.bedrock.enable_model_access():
        logging.error("Failed to enable Bedrock model access")
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


    logging.info("Listing and removing all managed policies")
    attached_policies = aws.iam.list_attached_managed_policies(role_name)
    for policy_arn in attached_policies:
        logging.info("Detaching managed policy: %s", policy_arn)
        if not aws.iam.detach_managed_policy(role_name, policy_arn):
            logging.error("Failed to detach managed policy: %s", policy_arn)
            return 1
        logging.info("Detached managed policy: %s", policy_arn)


    logging.info("Listing and removing all inline policies")
    inline_policies = aws.iam.list_inline_policies(role_name)
    for policy_name in inline_policies:
        logging.info("Deleting inline policy: %s", policy_name)
        if not aws.iam.delete_role_policy(role_name, policy_name):
            logging.error("Failed to delete inline policy: %s", policy_name)
            return 1
        logging.info("Deleted inline policy: %s", policy_name)


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
    state = detect_infrastructure_state(
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
        session_token=session_token
    )
    if not args.force:
        try:
            confirm = input("Are you sure you want to destroy all infrastructure resources? ([y]/n): ").strip().lower() or 'y'
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
    print("All infrastructure resources destroyed")
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
            logging.error("Required: AdministratorAccess or equivalent IAM permissions")
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

    logging.info("Validating OIDC role permissions...")
    admin_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
    if not aws_client.iam.managed_policy_attached(role_name, admin_arn):
        logging.error("FATAL: OIDC role '%s' missing AdministratorAccess managed policy", role_name)
        sys.exit(1)
    logging.info("✓ AdministratorAccess policy attached")
    logging.info("✓ OIDC role permissions validated")
def delete_github_secrets(github_token: str, github_org: str, github_repo: str,
                          secret_names: list) -> bool:

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
    access_key_id = getattr(args, 'aws_access_key_id', None)
    secret_access_key = getattr(args, 'aws_secret_access_key', None)
    if not access_key_id:
        access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    if not secret_access_key:
        secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    state = detect_infrastructure_state(
        args.aws_account_id,
        args.aws_region,
        args.aws_iam_role_name,
        access_key_id,
        secret_access_key
    )
    if state == 'warm' and is_workflow:
        logging.info("Using OIDC authentication (warm state)")
        oidc_creds = assume_role_with_oidc(args.aws_account_id, args.aws_region, args.aws_iam_role_name)
        if not oidc_creds:
            logging.error("Failed to assume role with OIDC")
            return None, None, None
        return oidc_creds['access_key_id'], oidc_creds['secret_access_key'], oidc_creds['session_token']
    if access_key_id and secret_access_key:
        logging.info("Using direct credentials")
        return access_key_id, secret_access_key, None
    logging.error("No credentials available")
    return None, None, None
def _check_readme_needs_update(bedrock: BedrockClient, source_code: str, current_readme: str, max_tokens: int = 200) -> bool:
    if not current_readme or not current_readme.strip():
        return True

    prompt = f"""You are a technical documentation expert. Your task is to determine if a README file needs to be updated based on the source code.

<source_code>
{source_code}
</source_code>

<current_readme>
{current_readme}
</current_readme>

CRITICAL ARCHITECTURE REQUIREMENTS TO CHECK:
- This script is SELF-CONTAINED and uses ONLY Python standard library (stdlib)
- NO external dependencies required (no pip install, no requirements.txt)
- NO AWS CLI required - implements AWS API calls using pure Python stdlib
- NO boto3 or other AWS SDKs - custom AWS client implementation using urllib and stdlib only

Check if the README has ANY issues, including but not limited to:
1. Title doesn't match actual infrastructure name (should be "AWS-GitHub Authentication Infrastructure" not "bootstrap" terminology)
2. Inconsistent or outdated terminology throughout the document (no "bootstrap" references)
3. Incorrectly mentions AWS CLI as a requirement or dependency (MAJOR ERROR)
4. Incorrectly mentions boto3, pip install, or requirements.txt (MAJOR ERROR)
5. Fails to emphasize the self-contained, dependency-free architecture
6. Inaccurate functionality, usage, or implementation details
7. Outdated command examples or file paths
8. Missing or incorrect architecture descriptions
9. Any other inaccuracies, inconsistencies, or outdated information

Does the README need updating? Respond with ONLY "true" or "false"."""
    response = bedrock.invoke_model(prompt, max_tokens=max_tokens)
    return response.strip().lower().startswith('true')
def _update_readme(bedrock: BedrockClient, source_code: str, max_tokens: int = 16000) -> str:
    prompt = f"""You are a technical documentation expert. Generate a comprehensive README.md file for the following Python script that manages AWS-GitHub authentication infrastructure.

<source_code>
{source_code}
</source_code>

CRITICAL REQUIREMENTS TO EMPHASIZE:
- This script is SELF-CONTAINED and uses ONLY Python standard library (stdlib)
- NO external dependencies required (no pip install, no requirements.txt)
- NO AWS CLI required - implements AWS API calls using pure Python stdlib
- NO boto3 or other AWS SDKs - custom AWS client implementation using urllib and stdlib only
- This is a key selling point and architectural decision - must be prominently featured

Create a professional README that includes:
1. Title "AWS-GitHub Authentication Infrastructure" emphasizing the self-contained, dependency-free nature
2. Purpose and what the script does
3. Requirements section:
   - List ONLY: Python 3.11+
   - DO NOT list: AWS CLI, boto3, pip, requirements.txt, or any external dependencies
   - Explicitly state: "No AWS CLI required - uses pure Python stdlib"
4. Usage instructions with command examples
5. Architecture overview (three-state system: COLD/WARM/DESTROY)
6. Configuration details
7. Authentication methods (OIDC vs direct credentials)
8. Implementation details: Pure Python stdlib implementation - custom AWS API clients without boto3
9. Security considerations
10. Troubleshooting tips

IMPORTANT: Do NOT include a "License" section. The repository already has a LICENSE.md file, so the README must not duplicate licensing information.

Format the README in clean, professional markdown. Be comprehensive but concise. Use code blocks for examples.
Generate ONLY the README content, starting with the title. Do not include any preamble or explanation."""
    try:
        return bedrock.invoke_model(prompt, max_tokens=max_tokens)
    except Exception as e:
        logging.error("Failed to generate README via Bedrock: %s", e)
        raise
def _read_file_safe(file_path: str, description: str) -> Optional[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except IOError as e:
        logging.error("Failed to read %s: %s", description, e)
        return None
def _handle_readme_check(args: argparse.Namespace, bedrock: 'BedrockClient',
                        source_code: str, current_readme: str, max_tokens: int) -> int:
    logging.info("Checking if README needs update via Bedrock...")
    needs_update = _check_readme_needs_update(bedrock, source_code, current_readme, max_tokens)
    readme_is_current = not needs_update
    logging.info("README is current" if readme_is_current else "README needs update")
    print(readme_is_current)
    if args.output_file:
        with open(args.output_file, 'a', encoding='utf-8') as f:
            f.write(f'readme_is_current={str(readme_is_current).lower()}\n')
    return 0
def _handle_readme_update(bedrock: 'BedrockClient', source_code: str, readme_path: str, max_tokens: int) -> int:
    logging.info("Generating updated README via Bedrock...")
    try:
        new_readme = _update_readme(bedrock, source_code, max_tokens)
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_readme)
        logging.info("Updated README written to %s", readme_path)
        print(f"README updated successfully: {readme_path}")
        return 0
    except (AWSHTTPError, urllib.error.URLError, urllib.error.HTTPError) as e:
        logging.error("Failed to generate README: %s", e)
        return 1
    except IOError as e:
        logging.error("Failed to write README: %s", e)
        return 1
def cmd_readme(args: argparse.Namespace) -> int:
    access_key, secret_key, session_token = _get_credentials_for_state(args)
    if not access_key:
        logging.error("Failed to obtain AWS credentials")
        return 1
    bedrock = BedrockClient(args.aws_region, access_key, secret_key, session_token)
    if hasattr(args, 'bedrock_model_id') and args.bedrock_model_id:
        bedrock.set_model_id(args.bedrock_model_id)
    script_path = os.path.abspath(__file__)
    source_code = _read_file_safe(script_path, "auth_between_aws_and_github.py")
    if source_code is None:
        return 1
    readme_path = os.path.join(os.path.dirname(script_path), 'README.md')
    current_readme = _read_file_safe(readme_path, "README.md") if os.path.exists(readme_path) else ""
    if current_readme is None:
        return 1
    max_tokens_check = int(getattr(args, 'max_tokens', None) or 200)
    max_tokens_generate = int(getattr(args, 'max_tokens_generate', None) or 16000)
    if args.check:
        return _handle_readme_check(args, bedrock, source_code, current_readme, max_tokens_check)
    if args.update:
        return _handle_readme_update(bedrock, source_code, readme_path, max_tokens_generate)
    logging.error("Either --check or --update must be specified")
    return 1
def _setup_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Manage AWS-GitHub authentication infrastructure for GitHub Actions workflows'
    )
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output (DEBUG level)')
    parser.add_argument('-q', '--quiet', action='store_true',
                       help='Quiet mode, only show errors')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    create_parser = subparsers.add_parser('create', help='Create AWS-GitHub authentication infrastructure')
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
    create_required.add_argument('--bedrock-model-id', required=True,
                                help='Bedrock model ID (e.g., us.anthropic.claude-haiku-4-5-20251001-v1:0)')
    destroy_parser = subparsers.add_parser('destroy', help='Destroy AWS-GitHub authentication infrastructure')
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
    readme_optional.add_argument('--bedrock-model-id',
                                help='Bedrock model ID for README operations')
    readme_optional.add_argument('--max-tokens', type=int,
                                help='Maximum output tokens for README check')
    readme_optional.add_argument('--max-tokens-generate', type=int,
                                help='Maximum output tokens for README generation')
    return parser
def _execute_command(args: argparse.Namespace) -> int:
    command_map = {'create': create_resources, 'destroy': destroy_resources, 'readme': cmd_readme}
    return command_map[args.command](args) if args.command in command_map else 1
def main():
    parser = _setup_argparse()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 1
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    try:
        return _execute_command(args)
    except KeyboardInterrupt:
        print("\n\nAborted by user")
        return 130
    except (AWSHTTPError, urllib.error.URLError, urllib.error.HTTPError, IOError, OSError) as e:
        logging.error("Unexpected error: %s", e, exc_info=True)
        return 1
if __name__ == '__main__':
    sys.exit(main())
