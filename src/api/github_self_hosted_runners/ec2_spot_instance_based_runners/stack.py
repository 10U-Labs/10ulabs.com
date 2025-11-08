"""
Infrastructure: EC2 Spot Instance Based GitHub Self-Hosted Runners API

Creates:
- API Gateway HTTP API with custom domain (api.10ulabs.com)
- Lambda function for handling API requests
- Route53 record for custom domain
- ACM certificate for HTTPS
"""
from typing import Dict, Any
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    aws_iam as iam,
    aws_logs as logs,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_certificatemanager as acm,
    aws_ec2 as ec2,
)
from constructs import Construct


class EC2SpotRunnerAPIStack(Stack):
    """CDK Stack for EC2 Spot Runner API."""

    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Import VPC from existing GitHub runners infrastructure
        vpc = ec2.Vpc.from_lookup(
            self, "ImportedVPC",
            vpc_name=config["vpc_name"]
        )

        # Get public subnets for EC2 instances
        subnet_ids = [subnet.subnet_id for subnet in vpc.public_subnets]

        # Import security group for runners
        runner_sg = ec2.SecurityGroup.from_lookup_by_name(
            self, "ImportedRunnerSecurityGroup",
            security_group_name=config["security_group_name"],
            vpc=vpc
        )

        # Lambda function for API handler
        api_lambda = lambda_.Function(
            self, "EC2SpotRunnerAPIHandler",
            function_name=config["lambda_function_name"],
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("src/api/github_self_hosted_runners/ec2_spot_instance_based_runners"),
            timeout=Duration.seconds(config["lambda"]["timeout_seconds"]),
            memory_size=config["lambda"]["memory_mb"],
            environment={
                "SUBNETS": ",".join(subnet_ids),
                "SECURITY_GROUPS": runner_sg.security_group_id,
                "EC2_AMI_ID": config["ec2"]["ami_id"],
                "EC2_INSTANCE_TYPES": ",".join(config["ec2"]["instance_types"]),
                "EC2_IAM_INSTANCE_PROFILE": config["ec2"]["iam_instance_profile"],
                "EC2_MAX_PRICE": str(config["ec2"]["max_price"]),
                "GITHUB_TOKEN_SECRET_NAME": config["github_token_secret_name"],
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="API handler for launching EC2 spot instance GitHub runners"
        )

        # Grant Lambda permissions to launch EC2 instances
        api_lambda.add_to_role_policy(
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

        # Grant Lambda permission to pass IAM role to EC2
        api_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                resources=[f"arn:aws:iam::{config['aws_account_id']}:role/{config['ec2']['iam_role_name']}"],
                conditions={
                    "StringEquals": {
                        "iam:PassedToService": "ec2.amazonaws.com"
                    }
                }
            )
        )

        # Grant Lambda permission to read GitHub token from Secrets Manager
        api_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[f"arn:aws:secretsmanager:{config['aws_region']}:{config['aws_account_id']}:secret:{config['github_token_secret_name']}-*"]
            )
        )

        # Lookup existing hosted zone from domain stack
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone",
            domain_name=config["hosted_zone_name"]
        )

        # ACM Certificate for api.10ulabs.com with DNS validation
        certificate = acm.Certificate(
            self, "APICertificate",
            domain_name=config["domain_name"],
            validation=acm.CertificateValidation.from_dns(hosted_zone)
        )

        # API Gateway HTTP API with custom domain
        domain_name_obj = apigw.DomainName(
            self, "APIDomainName",
            domain_name=config["domain_name"],
            certificate=certificate
        )

        http_api = apigw.HttpApi(
            self, "EC2SpotRunnerAPI",
            api_name=config["api_gateway_name"],
            description="API for launching EC2 spot instance GitHub self-hosted runners",
            default_domain_mapping=apigw.DomainMappingOptions(
                domain_name=domain_name_obj
            ),
            cors_preflight=apigw.CorsPreflightOptions(
                allow_origins=["*"],
                allow_methods=[apigw.CorsHttpMethod.POST],
                allow_headers=["Content-Type", "Authorization"]
            )
        )

        # Add API route
        http_api.add_routes(
            path="/v1/github-self-hosted-runners/ec2-spot-instance-based-runners",
            methods=[apigw.HttpMethod.POST],
            integration=integrations.HttpLambdaIntegration(
                "EC2SpotRunnerIntegration",
                api_lambda
            )
        )

        # Route53 A record for api.10ulabs.com pointing to API Gateway
        route53.ARecord(
            self, "APIARecord",
            zone=hosted_zone,
            record_name=config["domain_name"],
            target=route53.RecordTarget.from_alias(
                targets.ApiGatewayv2DomainProperties(
                    domain_name_obj.regional_domain_name,
                    domain_name_obj.regional_hosted_zone_id
                )
            )
        )

        # Outputs
        CfnOutput(
            self, "APIEndpoint",
            value=f"https://{config['domain_name']}/v1/github-self-hosted-runners/ec2-spot-instance-based-runners",
            description="API endpoint for launching EC2 spot runners"
        )

        CfnOutput(
            self, "LambdaFunctionName",
            value=api_lambda.function_name,
            description="Lambda function name for EC2 spot runner API"
        )

        CfnOutput(
            self, "APIGatewayId",
            value=http_api.api_id,
            description="API Gateway HTTP API ID"
        )
