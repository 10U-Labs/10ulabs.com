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


class ImageForDockerRunnerStack(Stack):
    def _create_lambda_function(self, config: Dict[str, Any]) -> lambda_.Function:
        github_token_secret_name = Fn.import_value("TenULabsApi-GitHubTokenSecretName")
        ecr_repository_name = Fn.import_value("TenULabsApi-ECRRepositoryName")

        return lambda_.Function(
            self, "ImageForDockerRunnerHandler",
            function_name=config["naming"]["lambda_function_name"],
            runtime=lambda_.Runtime.PYTHON_3_14,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("api/resources/image_for_docker_runner"),
            timeout=Duration.seconds(config["lambda"]["timeout_seconds"]),
            memory_size=config["lambda"]["memory_mb"],
            environment={
                "GITHUB_TOKEN": Fn.sub(
                    "{{resolve:secretsmanager:${SecretName}:SecretString:github_token}}",
                    {"SecretName": github_token_secret_name}
                ),
                "GITHUB_REPO": "10U-Labs-LLC/10ulabs.com",
                "ECR_REPOSITORY": ecr_repository_name,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Lambda handler for triggering Docker image builds via GitHub Actions"
        )

    def _configure_lambda_permissions(self, lambda_function: lambda_.Function, config: Dict[str, Any]) -> None:
        github_token_secret_name = Fn.import_value("TenULabsApi-GitHubTokenSecretName")
        ecr_repository_name = Fn.import_value("TenULabsApi-ECRRepositoryName")

        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[f"arn:aws:secretsmanager:{config['aws']['region']}:{config['aws']['account_id']}:secret:{github_token_secret_name}-*"]
            )
        )

        lambda_function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:DescribeImages",
                    "ecr:ListImages",
                    "ecr:BatchDeleteImage",
                    "ecr:BatchGetImage"
                ],
                resources=[f"arn:aws:ecr:{config['aws']['region']}:{config['aws']['account_id']}:repository/{ecr_repository_name}"]
            )
        )

    def _create_api_resources(self, lambda_function: lambda_.Function) -> apigw.Resource:
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

        image_resource = v1_resource.add_resource("image-for-docker-runner")
        image_resource.add_method(
            "POST",
            apigw.LambdaIntegration(lambda_function)
        )
        image_resource.add_method(
            "GET",
            apigw.LambdaIntegration(lambda_function)
        )

        latest_resource = image_resource.add_resource("latest")
        latest_resource.add_method(
            "GET",
            apigw.LambdaIntegration(lambda_function)
        )

        digest_resource = image_resource.add_resource("{digest}")
        digest_resource.add_method(
            "DELETE",
            apigw.LambdaIntegration(lambda_function)
        )

        return image_resource

    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        lambda_function = self._create_lambda_function(config)
        self._configure_lambda_permissions(lambda_function, config)
        self._create_api_resources(lambda_function)

        CfnOutput(
            self, "ImageForDockerRunnerEndpoint",
            value=f"https://{config['domain_names']['subdomain']}/v1/image-for-docker-runner",
            description="API endpoint for triggering Docker image builds"
        )

        CfnOutput(
            self, "ImageForDockerRunnerLambdaName",
            value=lambda_function.function_name,
            description="Lambda function name for image builder"
        )
