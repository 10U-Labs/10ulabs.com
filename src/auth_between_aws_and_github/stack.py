from aws_cdk import (
    Stack,
    CfnOutput,
    CustomResource,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_ssm as ssm,
)
from constructs import Construct

class AuthBetweenAwsAndGithubStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

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

        oidc_provider_lambda = lambda_.Function(
            self, 'OIDCProviderLambda',
            runtime=lambda_.Runtime.PYTHON_3_14,
            handler='index.handler',
            code=lambda_.Code.from_inline('''
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
'''),
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

        iam_role_lambda_role = iam.Role(
            self, 'IAMRoleLambdaRole',
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole')
            ],
            inline_policies={
                'IAMRoleManagement': iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            actions=[
                                'iam:CreateRole',
                                'iam:GetRole',
                                'iam:DeleteRole',
                                'iam:AttachRolePolicy',
                                'iam:DetachRolePolicy',
                                'iam:PutRolePolicy',
                                'iam:DeleteRolePolicy',
                                'iam:UpdateAssumeRolePolicy'
                            ],
                            resources=['*']
                        )
                    ]
                )
            }
        )

        iam_role_lambda = lambda_.Function(
            self, 'IAMRoleLambda',
            runtime=lambda_.Runtime.PYTHON_3_14,
            handler='index.handler',
            code=lambda_.Code.from_inline('''
import boto3
import cfnresponse
import json

iam = boto3.client('iam')

def handler(event, context):
    try:
        request_type = event['RequestType']
        role_name = event['ResourceProperties']['RoleName']
        provider_arn = event['ResourceProperties']['ProviderArn']
        github_org = event['ResourceProperties']['GitHubOrg']
        github_repo = event['ResourceProperties']['GitHubRepo']

        account_id = context.invoked_function_arn.split(':')[4]
        role_arn = f"arn:aws:iam::{account_id}:role/{role_name}"

        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {"Federated": provider_arn},
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

        if request_type == 'Create':
            try:
                existing_role = iam.get_role(RoleName=role_name)
                print(f"IAM role already exists: {role_arn}")
                iam.update_assume_role_policy(
                    RoleName=role_name,
                    PolicyDocument=json.dumps(trust_policy)
                )
                print(f"Updated trust policy for existing role")
            except iam.exceptions.NoSuchEntityException:
                iam.create_role(
                    RoleName=role_name,
                    AssumeRolePolicyDocument=json.dumps(trust_policy),
                    Description=f"GitHub Actions role for {github_org}/{github_repo}"
                )
                print(f"Created IAM role: {role_arn}")

            try:
                iam.attach_role_policy(
                    RoleName=role_name,
                    PolicyArn='arn:aws:iam::aws:policy/AdministratorAccess'
                )
                print(f"Attached AdministratorAccess policy")
            except Exception as e:
                if 'already attached' not in str(e).lower():
                    raise
                print(f"AdministratorAccess policy already attached")

            cfnresponse.send(event, context, cfnresponse.SUCCESS, {'Arn': role_arn}, role_arn)

        elif request_type == 'Update':
            try:
                iam.update_assume_role_policy(
                    RoleName=role_name,
                    PolicyDocument=json.dumps(trust_policy)
                )
                print(f"Updated trust policy")
            except Exception as e:
                print(f"Update warning: {str(e)}")
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {'Arn': role_arn}, role_arn)

        elif request_type == 'Delete':
            cfnresponse.send(event, context, cfnresponse.SUCCESS, {})

    except Exception as e:
        print(f"Error: {str(e)}")
        cfnresponse.send(event, context, cfnresponse.FAILED, {}, str(e))
'''),
            role=iam_role_lambda_role
        )

        iam_role_resource = CustomResource(
            self, 'GitHubActionsRole',
            service_token=iam_role_lambda.function_arn,
            properties={
                'RoleName': config['aws']['iam_role_name'],
                'ProviderArn': provider_arn,
                'GitHubOrg': config['github']['org'],
                'GitHubRepo': config['github']['repo']
            }
        )

        role_arn = iam_role_resource.get_att_string('Arn')

        parameter = ssm.StringParameter(
            self, 'GitHubPATParameter',
            parameter_name=f"/github-runner/credentials",
            string_value="PLACEHOLDER_WILL_BE_UPDATED",
            description="GitHub Personal Access Token for runner authentication",
            tier=ssm.ParameterTier.STANDARD
        )

        self.role_arn = role_arn
        self.parameter_arn = parameter.parameter_arn
        self.provider_arn = provider_arn

        CfnOutput(
            self, "GitHubPATParameterName",
            value=parameter.parameter_name,
            export_name="GitHubAuth-PATSecretName",
            description="GitHub Personal Access Token parameter name in SSM Parameter Store"
        )
