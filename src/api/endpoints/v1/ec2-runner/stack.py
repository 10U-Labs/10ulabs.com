from typing import Dict, Any
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    Fn,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct


class EC2RunnerStack(Stack):
    def _create_lambda_function(self, config: Dict[str, Any]) -> lambda_.Function:
        vpc_public_subnet_ids = Fn.import_value("TenULabsApi-PublicSubnetIds")
        runner_sg_id = Fn.import_value("TenULabsApi-RunnerSecurityGroupId")
        github_token_secret_name = Fn.import_value("TenULabsApi-GitHubTokenSecretName")
        ec2_instance_profile_name = Fn.import_value("TenULabsApi-EC2InstanceProfileName")

        return lambda_.Function(
            self, "EC2RunnerHandler",
            function_name=config["naming"]["lambda_function_name"],
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("api/resources/ec2_runner"),
            timeout=Duration.seconds(config["lambda"]["timeout_seconds"]),
            memory_size=config["lambda"]["memory_mb"],
            environment={
                "SUBNETS": vpc_public_subnet_ids,
                "SECURITY_GROUPS": runner_sg_id,
                "EC2_AMI_ID": config["ec2"]["ami_id"],
                "EC2_INSTANCE_TYPES": ",".join(config["ec2"]["instance_types"]),
                "EC2_IAM_INSTANCE_PROFILE": ec2_instance_profile_name,
                "EC2_MAX_PRICE": str(config["ec2"]["max_price"]),
                "GITHUB_TOKEN_SECRET_NAME": github_token_secret_name,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Lambda handler for launching EC2 spot instance GitHub runners"
        )

    def _configure_lambda_permissions(self, ec2_runner_lambda: lambda_.Function, config: Dict[str, Any]) -> None:
        github_token_secret_name = Fn.import_value("TenULabsApi-GitHubTokenSecretName")
        ec2_runner_role_name = Fn.import_value("TenULabsApi-EC2RunnerRoleName")

        ec2_runner_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:RunInstances",
                    "ec2:TerminateInstances",
                    "ec2:CreateTags",
                    "ec2:DescribeInstances",
                    "ec2:DescribeImages",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeSecurityGroups"
                ],
                resources=["*"]
            )
        )

        ec2_runner_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                resources=[f"arn:aws:iam::{config['aws']['account_id']}:role/{ec2_runner_role_name}"],
                conditions={
                    "StringEquals": {
                        "iam:PassedToService": "ec2.amazonaws.com"
                    }
                }
            )
        )

        ec2_runner_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[f"arn:aws:secretsmanager:{config['aws']['region']}:{config['aws']['account_id']}:secret:{github_token_secret_name}-*"]
            )
        )

    def _create_api_resources(self, ec2_runner_lambda: lambda_.Function) -> apigw.Resource:
        rest_api_id = Fn.import_value("TenULabsApi-RestApiId")
        v1_resource_id = Fn.import_value("TenULabsApi-V1ResourceId")

        rest_api = apigw.RestApi.from_rest_api_attributes(
            self, "ImportedApi",
            rest_api_id=rest_api_id,
            root_resource_id=Fn.import_value("TenULabsApi-RootResourceId")
        )

        v1_resource = apigw.Resource.from_resource_attributes(
            self, "V1Resource",
            resource_id=v1_resource_id,
            rest_api=rest_api,
            path="/v1"
        )

        ec2_runner_resource = v1_resource.add_resource("ec2-runner")
        ec2_runner_resource.add_method(
            "POST",
            apigw.LambdaIntegration(ec2_runner_lambda)
        )
        return ec2_runner_resource

    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        ec2_runner_lambda = self._create_lambda_function(config)
        self._configure_lambda_permissions(ec2_runner_lambda, config)
        self._create_api_resources(ec2_runner_lambda)

        CfnOutput(
            self, "EC2RunnerEndpoint",
            value=f"https://{config['domain_names']['subdomain']}/v1/ec2-runner",
            description="API endpoint for launching EC2 spot runners"
        )

        CfnOutput(
            self, "EC2RunnerLambdaName",
            value=ec2_runner_lambda.function_name,
            description="Lambda function name for EC2 runner handler"
        )
