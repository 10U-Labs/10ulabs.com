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


class DockerRunnerStack(Stack):
    def _create_lambda_function(self, config: Dict[str, Any]) -> lambda_.Function:
        vpc_public_subnet_ids = Fn.import_value("TenULabsApi-PublicSubnetIds")
        runner_sg_id = Fn.import_value("TenULabsApi-RunnerSecurityGroupId")
        cluster_arn = Fn.import_value("TenULabsApi-ClusterArn")
        task_definition_arn = Fn.import_value("TenULabsApi-TaskDefinitionArn")
        github_token_secret_name = Fn.import_value("TenULabsApi-GitHubTokenSecretName")
        ecr_repository_name = Fn.import_value("TenULabsApi-ECRRepositoryName")

        return lambda_.Function(
            self, "DockerRunnerHandler",
            function_name=config["naming"]["lambda_function_name"],
            runtime=lambda_.Runtime.PYTHON_3_14,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset("api/resources/docker_runner"),
            timeout=Duration.seconds(config["lambda"]["timeout_seconds"]),
            memory_size=config["lambda"]["memory_mb"],
            environment={
                "SUBNETS": vpc_public_subnet_ids,
                "SECURITY_GROUPS": runner_sg_id,
                "ECS_CLUSTER": cluster_arn,
                "TASK_DEFINITION": task_definition_arn,
                "GITHUB_TOKEN_SECRET_NAME": github_token_secret_name,
                "ECR_REPOSITORY": ecr_repository_name,
                "IMAGE_API_ENDPOINT": f"https://{config['domain_names']['subdomain']}",
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Lambda handler for launching Fargate spot GitHub runners"
        )

    def _configure_lambda_permissions(self, docker_runner_lambda: lambda_.Function, config: Dict[str, Any]) -> None:
        github_token_secret_name = Fn.import_value("TenULabsApi-GitHubTokenSecretName")
        ecr_repository_name = Fn.import_value("TenULabsApi-ECRRepositoryName")

        docker_runner_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ecs:RunTask",
                    "ecs:DescribeTasks",
                    "ecs:ListTasks",
                    "ecs:StopTask"
                ],
                resources=["*"]
            )
        )

        docker_runner_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                resources=[
                    Fn.import_value("TenULabsApi-TaskRoleArn"),
                    Fn.import_value("TenULabsApi-ExecutionRoleArn")
                ]
            )
        )

        docker_runner_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[f"arn:aws:secretsmanager:{config['aws']['region']}:{config['aws']['account_id']}:secret:{github_token_secret_name}-*"]
            )
        )

        docker_runner_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ecr:DescribeImages",
                    "ecr:ListImages",
                    "ecr:BatchGetImage",
                    "ecr:GetDownloadUrlForLayer"
                ],
                resources=[f"arn:aws:ecr:{config['aws']['region']}:{config['aws']['account_id']}:repository/{ecr_repository_name}"]
            )
        )

    def _create_api_resources(self, docker_runner_lambda: lambda_.Function) -> apigw.Resource:
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

        docker_runner_resource = v1_resource.add_resource("docker-runner")
        docker_runner_resource.add_method(
            "POST",
            apigw.LambdaIntegration(docker_runner_lambda)
        )
        docker_runner_resource.add_method(
            "GET",
            apigw.LambdaIntegration(docker_runner_lambda)
        )

        latest_resource = docker_runner_resource.add_resource("latest")
        latest_resource.add_method(
            "GET",
            apigw.LambdaIntegration(docker_runner_lambda)
        )

        return docker_runner_resource

    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        docker_runner_lambda = self._create_lambda_function(config)
        self._configure_lambda_permissions(docker_runner_lambda, config)
        self._create_api_resources(docker_runner_lambda)

        CfnOutput(
            self, "DockerRunnerEndpoint",
            value=f"https://{config['domain_names']['subdomain']}/v1/docker-runner",
            description="API endpoint for launching Fargate spot runners"
        )

        CfnOutput(
            self, "DockerRunnerLambdaName",
            value=docker_runner_lambda.function_name,
            description="Lambda function name for Docker runner handler"
        )
