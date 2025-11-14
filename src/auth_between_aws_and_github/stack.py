from aws_cdk import (
    Stack,
    CustomResource,
    aws_iam as iam,
    aws_lambda as lambda_,
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

        oidc_lambda_role = iam.Role(
            self, 'OIDCProviderLambdaRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
            ],
            inline_policies={
                'OIDCProviderManagement': iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                'iam:CreateOpenIDConnectProvider',
                                'iam:GetOpenIDConnectProvider',
                                'iam:DeleteOpenIDConnectProvider',
                                'iam:ListOpenIDConnectProviders'
                            ],
                            resources=['*']
                        )
                    ]
                )
            }
        )

        oidc_provider_lambda_code = '''
import boto3
import cfnresponse

iam = boto3.client('iam')

def handler(event, context):
    try:
        request_type = event['RequestType']
        url = event['ResourceProperties']['Url']
        client_ids = event['ResourceProperties']['ClientIds']
        thumbprints = event['ResourceProperties']['Thumbprints']

        provider_arn = f"arn:aws:iam::{context.invoked_function_arn.split(':')[4]}:oidc-provider/{url.replace('https://', '')}"

        if request_type == 'Create':
            try:
                iam.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
                print(f"OIDC provider already exists: {provider_arn}")
            except iam.exceptions.NoSuchEntityException:
                response = iam.create_open_id_connect_provider(
                    Url=url,
                    ClientIDList=client_ids,
                    ThumbprintList=thumbprints
                )
                provider_arn = response['OpenIDConnectProviderArn']
                print(f"Created OIDC provider: {provider_arn}")

            cfnresponse.send(event, context, cfnresponse.SUCCESS, {'Arn': provider_arn}, provider_arn)

        elif request_type == 'Update':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {'Arn': provider_arn}, provider_arn)

        elif request_type == 'Delete':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})

    except Exception as e:
        print(f"Error: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, str(e))
'''

        oidc_provider_lambda = lambda_.Function(
            self, 'OIDCProviderLambda',
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler='index.handler',
            code=lambda_.Code.from_inline(oidc_provider_lambda_code),
            role=oidc_lambda_role
        )

        oidc_provider_resource = CustomResource(
            self, 'GitHubOIDCProvider',
            service_token=oidc_provider_lambda.function_arn,
            properties={
                'Url': 'https://token.actions.githubusercontent.com',
                'ClientIds': ['sts.amazonaws.com'],
                'Thumbprints': ['6938fd4d98bab03faadb97b34396831e3780aea1']
            }
        )

        provider_arn = oidc_provider_resource.get_att_string('Arn')

        role = iam.Role(
            self, 'GitHubActionsRole',
            role_name=role_name,
            assumed_by=iam.WebIdentityPrincipal(
                provider_arn,
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

        secret = secretsmanager.Secret.from_secret_name_v2(
            self, 'GitHubPATSecret',
            secret_name=secret_name
        )

        self.role_arn = role.role_arn
        self.secret_arn = secret.secret_arn
        self.provider_arn = provider_arn
