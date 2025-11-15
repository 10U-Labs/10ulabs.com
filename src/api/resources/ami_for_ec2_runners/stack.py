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


class AmiForEC2RunnersStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        rest_api_id = Fn.import_value("TenULabsApi-RestApiId")
        v1_resource_id = Fn.import_value("TenULabsApi-V1ResourceId")
        vpc_id = Fn.import_value("TenULabsApi-VpcId")
        vpc_public_subnet_ids = Fn.import_value("TenULabsApi-PublicSubnetIds")
        runner_sg_id = Fn.import_value("TenULabsApi-RunnerSecurityGroupId")

        ami_builder_lambda = lambda_.Function(
            self, "AmiBuilderHandler",
            function_name=config["naming"]["lambda_function_name"],
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("api/resources/ami_for_ec2_runners"),
            timeout=Duration.seconds(config["lambda"]["timeout_seconds"]),
            memory_size=config["lambda"]["memory_mb"],
            environment={
                "VPC_ID": vpc_id,
                "SUBNETS": vpc_public_subnet_ids,
                "SECURITY_GROUPS": runner_sg_id,
                "BUILDER_AMI_ID": config["packer"]["builder_ami_id"],
                "PACKER_INSTANCE_TYPES": ",".join(config["packer"]["instance_types"]),
                "PACKER_INSTANCE_PROFILE": config["packer"]["iam_instance_profile"],
                "PACKER_MAX_PRICE": str(config["packer"]["max_price"]),
                "PACKER_CONFIG_BUCKET": config["packer"]["config_bucket"],
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Lambda handler for building GitHub runner AMIs with Packer"
        )

        ami_builder_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:RunInstances",
                    "ec2:TerminateInstances",
                    "ec2:CreateTags",
                    "ec2:DescribeInstances",
                    "ec2:DescribeImages",
                    "ec2:DeregisterImage",
                    "ec2:DeleteSnapshot",
                    "ec2:DescribeSnapshots",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeSecurityGroups"
                ],
                resources=["*"]
            )
        )

        ami_builder_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                resources=[f"arn:aws:iam::{config['aws']['account_id']}:role/{config['packer']['iam_role_name']}"],
                conditions={
                    "StringEquals": {
                        "iam:PassedToService": "ec2.amazonaws.com"
                    }
                }
            )
        )

        ami_builder_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:GetObject",
                    "s3:ListBucket"
                ],
                resources=[
                    f"arn:aws:s3:::{config['packer']['config_bucket']}",
                    f"arn:aws:s3:::{config['packer']['config_bucket']}/*"
                ]
            )
        )

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

        ami_resource = v1_resource.add_resource("ami-for-ec2-runners")

        ami_resource.add_method(
            "POST",
            apigw.LambdaIntegration(ami_builder_lambda)
        )

        ami_resource.add_method(
            "GET",
            apigw.LambdaIntegration(ami_builder_lambda)
        )

        ami_id_resource = ami_resource.add_resource("{ami_id}")
        ami_id_resource.add_method(
            "DELETE",
            apigw.LambdaIntegration(ami_builder_lambda)
        )

        CfnOutput(
            self, "AmiBuilderEndpoint",
            value=f"https://{config['domain_names']['subdomain']}/v1/ami-for-ec2-runners",
            description="API endpoint for building GitHub runner AMIs"
        )

        CfnOutput(
            self, "AmiBuilderLambdaName",
            value=ami_builder_lambda.function_name,
            description="Lambda function name for AMI builder"
        )
