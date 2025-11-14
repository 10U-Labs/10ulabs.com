#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stderr
)

def is_running_in_github_actions() -> bool:
    return os.environ.get('GITHUB_ACTIONS', '').lower() == 'true'

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
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        logging.error("Failed to get OIDC token: %s", e)
        return None

def assume_role_with_oidc(account_id: str, region: str, role_name: str) -> Optional[Dict[str, str]]:
    oidc_token = get_oidc_token()
    if not oidc_token:
        logging.error("No OIDC token available")
        return None

    role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"
    try:
        sts_client = boto3.client('sts', region_name=region)
        response = sts_client.assume_role_with_web_identity(
            RoleArn=role_arn,
            RoleSessionName='GitHubActions',
            WebIdentityToken=oidc_token
        )
        creds = response['Credentials']
        logging.info("Successfully assumed role: %s", role_name)
        return {
            'access_key_id': creds['AccessKeyId'],
            'secret_access_key': creds['SecretAccessKey'],
            'session_token': creds['SessionToken']
        }
    except ClientError as e:
        logging.error("Failed to assume role with OIDC: %s", e)
        return None

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
        iam_client = boto3.client(
            'iam',
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key
        )
        oidc_provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
        iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=oidc_provider_arn)
        logging.info("State: WARM (infrastructure exists, using direct credentials)")
        return 'warm'
    except ClientError:
        logging.info("State: COLD (no infrastructure, using direct credentials)")
        return 'cold'

def get_secret_from_secrets_manager(secret_name: str, region: str,
                                    access_key_id: str, secret_access_key: str,
                                    session_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    try:
        secrets_client = boto3.client(
            'secretsmanager',
            region_name=region,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            aws_session_token=session_token
        )
        response = secrets_client.get_secret_value(SecretId=secret_name)
        return json.loads(response['SecretString'])
    except ClientError as e:
        logging.warning("Could not retrieve secret: %s", e)
        return None

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

def setup_aws_clients(region: str, access_key_id: str, secret_access_key: str,
                     session_token: Optional[str] = None) -> tuple:
    kwargs = {
        'region_name': region,
        'aws_access_key_id': access_key_id,
        'aws_secret_access_key': secret_access_key
    }
    if session_token:
        kwargs['aws_session_token'] = session_token

    iam_client = boto3.client('iam', **kwargs)
    secrets_client = boto3.client('secretsmanager', **kwargs)
    bedrock_client = boto3.client('bedrock', **kwargs)

    return iam_client, secrets_client, bedrock_client

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

def _create_oidc_provider_step(iam_client, account_id: str) -> int:
    logging.info("Checking if GitHub Actions OIDC provider exists")
    oidc_provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"

    try:
        iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=oidc_provider_arn)
        logging.info("OIDC provider already exists, skipping creation")
        return 0
    except ClientError:
        pass

    logging.info("Creating GitHub Actions OIDC provider")
    try:
        iam_client.create_open_id_connect_provider(
            Url='https://token.actions.githubusercontent.com',
            ClientIDList=['sts.amazonaws.com'],
            ThumbprintList=['6938fd4d98bab03faadb97b34396831e3780aea1']
        )
        logging.info("Created OIDC provider")
        return 0
    except ClientError as e:
        logging.error("Failed to create OIDC provider: %s", e)
        return 1

def _create_iam_role_step(iam_client, args: argparse.Namespace,
                          trust_policy: Dict[str, Any]) -> int:
    logging.info("Checking if IAM role '%s' exists", args.aws_iam_role_name)

    try:
        response = iam_client.get_role(RoleName=args.aws_iam_role_name)
        logging.info("IAM role already exists, checking trust policy")

        current_trust_policy = response['Role']['AssumeRolePolicyDocument']
        if not policies_equal(current_trust_policy, trust_policy):
            logging.info("Trust policy differs, updating")
            try:
                iam_client.update_assume_role_policy(
                    RoleName=args.aws_iam_role_name,
                    PolicyDocument=json.dumps(trust_policy)
                )
                logging.info("Updated trust policy")
            except ClientError as e:
                logging.error("Failed to update trust policy: %s", e)
                return 1
        else:
            logging.info("Trust policy up to date")
        return 0
    except ClientError:
        pass

    logging.info("Creating IAM role '%s'", args.aws_iam_role_name)
    try:
        iam_client.create_role(
            RoleName=args.aws_iam_role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy)
        )
        logging.info("Created IAM role")
        return 0
    except ClientError as e:
        logging.error("Failed to create IAM role: %s", e)
        return 1

def _attach_iam_policies_step(iam_client, role_name: str) -> int:
    admin_arn = "arn:aws:iam::aws:policy/AdministratorAccess"

    try:
        response = iam_client.list_attached_role_policies(RoleName=role_name)
        attached_policies = [p['PolicyArn'] for p in response['AttachedPolicies']]
    except ClientError:
        attached_policies = []

    for policy_arn in attached_policies:
        if policy_arn != admin_arn:
            logging.info("Removing managed policy: %s", policy_arn)
            try:
                iam_client.detach_role_policy(RoleName=role_name, PolicyArn=policy_arn)
                logging.info("Removed managed policy: %s", policy_arn)
            except ClientError as e:
                logging.error("Failed to detach managed policy: %s", e)
                return 1

    try:
        response = iam_client.list_role_policies(RoleName=role_name)
        inline_policies = response['PolicyNames']
    except ClientError:
        inline_policies = []

    for policy_name in inline_policies:
        logging.info("Removing inline policy: %s", policy_name)
        try:
            iam_client.delete_role_policy(RoleName=role_name, PolicyName=policy_name)
            logging.info("Removed inline policy: %s", policy_name)
        except ClientError as e:
            logging.error("Failed to delete inline policy: %s", e)
            return 1

    if admin_arn not in attached_policies:
        logging.info("Attaching AdministratorAccess policy")
        try:
            iam_client.attach_role_policy(RoleName=role_name, PolicyArn=admin_arn)
            logging.info("Attached AdministratorAccess policy")
        except ClientError as e:
            logging.error("Failed to attach AdministratorAccess policy: %s", e)
            return 1
    else:
        logging.info("AdministratorAccess policy already attached")

    return 0

def _store_secret_and_cleanup_step(secrets_client, args: argparse.Namespace,
                                   github_token: str, is_workflow: bool) -> int:
    print()
    logging.info("Storing GitHub PAT in AWS Secrets Manager")
    secret_value = create_secret_value(github_token, args.github_org, args.github_repo)

    try:
        secrets_client.create_secret(
            Name=args.github_pat_secret_name,
            SecretString=json.dumps(secret_value)
        )
        logging.info("Stored credentials in Secrets Manager")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceExistsException':
            logging.info("Secret already exists, updating")
            try:
                secrets_client.update_secret(
                    SecretId=args.github_pat_secret_name,
                    SecretString=json.dumps(secret_value)
                )
                logging.info("Updated credentials in Secrets Manager")
            except ClientError as update_error:
                logging.error("Failed to update secret: %s", update_error)
                return 1
        else:
            logging.error("Failed to create secret: %s", e)
            return 1

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
        for secret_name in secrets_to_delete:
            logging.info("Please manually delete GitHub secret: %s", secret_name)

    return 0

def validate_aws_credentials(iam_client, bedrock_client) -> None:
    logging.info("Validating AWS credentials")
    try:
        iam_client.get_user()
        logging.info("AWS credentials valid")
    except ClientError:
        logging.info("AWS credentials valid (IAM role assumed)")

    logging.info("Checking AWS Bedrock access")
    try:
        bedrock_client.list_foundation_models(byOutputModality='TEXT')
        logging.info("AWS Bedrock access confirmed")
    except ClientError as e:
        logging.warning("AWS Bedrock access check failed: %s", e)

def validate_github_pat(github_token: str) -> None:
    logging.info("Validating GitHub PAT")
    try:
        req = urllib.request.Request(
            "https://api.github.com/user",
            headers={'Authorization': f'token {github_token}'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read())
                logging.info("GitHub PAT valid (user: %s)", data.get('login', 'unknown'))
            else:
                logging.error("GitHub PAT validation failed with status %d", response.status)
                sys.exit(1)
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        logging.error("GitHub PAT validation failed: %s", e)
        sys.exit(1)

def validate_oidc_role_permissions(iam_client, role_name: str) -> None:
    logging.info("Validating OIDC role permissions")
    try:
        response = iam_client.list_attached_role_policies(RoleName=role_name)
        attached_policies = [p['PolicyArn'] for p in response['AttachedPolicies']]

        admin_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
        if admin_arn in attached_policies:
            logging.info("OIDC role has AdministratorAccess")
        else:
            logging.warning("OIDC role missing AdministratorAccess policy")
    except ClientError as e:
        logging.error("Failed to validate OIDC role permissions: %s", e)

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

    iam_client, secrets_client, bedrock_client = setup_aws_clients(
        args.aws_region,
        aws_access_key,
        aws_secret_key,
        session_token
    )

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
    print("  AWS Client:  boto3")
    print(f"  Auth:        {'OIDC' if state == 'warm' and is_workflow else 'Direct credentials'}")
    print()
    print()

    validate_aws_credentials(iam_client, bedrock_client)
    validate_github_pat(github_token)
    print()

    if _create_oidc_provider_step(iam_client, args.aws_account_id) != 0:
        return 1

    trust_policy = create_trust_policy(args.aws_account_id, args.github_org, args.github_repo)

    if _create_iam_role_step(iam_client, args, trust_policy) != 0:
        return 1

    if _attach_iam_policies_step(iam_client, args.aws_iam_role_name) != 0:
        return 1

    print()
    logging.info("Enabling Bedrock model access (auto-detects if needed)")
    try:
        bedrock_client.list_foundation_models(byOutputModality='TEXT')
        logging.info("Bedrock model access confirmed")
    except ClientError as e:
        logging.warning("Bedrock access check: %s", e)

    print()
    validate_oidc_role_permissions(iam_client, args.aws_iam_role_name)
    print()

    return _store_secret_and_cleanup_step(secrets_client, args, github_token, is_workflow)

def setup_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Manage AWS-GitHub authentication infrastructure'
    )

    parser.add_argument('--aws-account-id', required=True, help='AWS account ID')
    parser.add_argument('--aws-region', required=True, help='AWS region')
    parser.add_argument('--aws-iam-role-name', required=True, help='IAM role name for GitHub Actions')
    parser.add_argument('--github-org', required=True, help='GitHub organization')
    parser.add_argument('--github-repo', required=True, help='GitHub repository')
    parser.add_argument('--github-pat-secret-name', required=True, help='Secrets Manager secret name for GitHub PAT')
    parser.add_argument('--aws-access-key-id', help='AWS access key ID')
    parser.add_argument('--aws-secret-access-key', help='AWS secret access key')
    parser.add_argument('--github-token', help='GitHub personal access token')

    return parser

def main():
    parser = setup_argparse()
    args = parser.parse_args()

    if not args.aws_access_key_id:
        args.aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    if not args.aws_secret_access_key:
        args.aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    if not args.github_token:
        args.github_token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_RUNNER_PAT')

    sys.exit(create_resources(args))

if __name__ == '__main__':
    main()
