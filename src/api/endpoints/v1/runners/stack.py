import os
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


class RunnersStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        rest_api_id = Fn.import_value("TenULabsApi-RestApiId")
        v1_resource_id = Fn.import_value("TenULabsApi-V1ResourceId")
        webhook_secret_name = Fn.import_value("TenULabsApi-WebhookSecretName")

        webhook_router_lambda = lambda_.Function(
            self, "WebhookRouterHandler",
            function_name=config["aws"]["lambda"]["function_name"],
            runtime=lambda_.Runtime.PYTHON_3_14,
            handler="webhook_router.lambda_handler",
            code=lambda_.Code.from_asset(os.path.dirname(__file__)),
            timeout=Duration.seconds(config["aws"]["lambda"]["timeout_seconds"]),
            memory_size=config["aws"]["lambda"]["memory_mb"],
            environment={
                "WEBHOOK_SECRET_NAME": webhook_secret_name,
                "API_BASE_URL": f"https://{config['domain_names']['fqdn']}",
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="GitHub webhook router for GitHub self-hosted runners"
        )

        webhook_router_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[f"arn:aws:secretsmanager:{config['aws']['region']}:{config['aws']['account_id']}:secret:{webhook_secret_name}-*"]
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

        runners_resource = v1_resource.add_resource("runners")
        runners_resource.add_method(
            "POST",
            apigw.LambdaIntegration(webhook_router_lambda)
        )

        CfnOutput(
            self, "RunnersWebhookEndpoint",
            value=f"https://{config['domain_names']['fqdn']}/v1/runners",
            description="GitHub webhook endpoint for runner routing"
        )

        CfnOutput(
            self, "WebhookRouterLambdaName",
            value=webhook_router_lambda.function_name,
            description="Lambda function name for webhook router"
        )
