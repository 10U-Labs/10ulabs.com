import json
import time
from aws_cdk import (
    Stack,
    SecretValue,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

class AuthBetweenAwsAndGithubStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        github_org = config['github']['org']
        github_repo = config['github']['repo']
        role_name = config['aws']['iam_role_name']
        secret_name = config['aws']['secrets_manager']['github_pat_secret_name']

        provider = iam.OpenIdConnectProvider(
            self, 'GitHubOIDCProvider',
            url='https://token.actions.githubusercontent.com',
            client_ids=['sts.amazonaws.com'],
            thumbprints=['6938fd4d98bab03faadb97b34396831e3780aea1']
        )

        role = iam.Role(
            self, 'GitHubActionsRole',
            role_name=role_name,
            assumed_by=iam.WebIdentityPrincipal(
                provider.open_id_connect_provider_arn,
                conditions={
                    'StringEquals': {
                        'token.actions.githubusercontent.com:aud': 'sts.amazonaws.com'
                    },
                    'StringLike': {
                        'token.actions.githubusercontent.com:sub':
                            f'repo:{github_org}/{github_repo}:*'
                    }
                }
            ),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('AdministratorAccess')
            ]
        )

        github_token = self.node.try_get_context('github_token')

        if github_token:
            secret_value = {
                "auth_method": "classic-pat",
                "github_token": github_token,
                "github_org": github_org,
                "github_repo": github_repo,
                "created_by": "cdk-deploy",
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            secret = secretsmanager.Secret(
                self, 'GitHubPATSecret',
                secret_name=secret_name,
                description=f'GitHub PAT for {github_org}/{github_repo} authentication',
                secret_string_value=SecretValue.unsafe_plain_text(json.dumps(secret_value))
            )
        else:
            secret = secretsmanager.Secret(
                self, 'GitHubPATSecret',
                secret_name=secret_name,
                description=f'GitHub PAT for {github_org}/{github_repo} authentication'
            )

        self.role_arn = role.role_arn
        self.secret_arn = secret.secret_arn
        self.provider_arn = provider.open_id_connect_provider_arn
