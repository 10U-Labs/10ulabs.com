import os
from typing import Dict, Any
from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    Fn,
    CustomResource,
    aws_lambda as lambda_,
    aws_lambda_event_sources as lambda_events,
    aws_apigateway as apigw,
    aws_iam as iam,
    aws_logs as logs,
    aws_sqs as sqs,
    aws_dynamodb as dynamodb,
    aws_cloudwatch as cloudwatch,
    aws_cloudwatch_actions as cw_actions,
    aws_sns as sns,
    custom_resources as cr,
)
from constructs import Construct


class RunnersStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        rest_api_id = Fn.import_value("TenULabsApi-RestApiId")
        v1_resource_id = Fn.import_value("TenULabsApi-V1ResourceId")
        webhook_secret_name = Fn.import_value("TenULabsApi-WebhookSecretName")
        github_pat_secret_name = Fn.import_value("GitHubAuth-PATSecretName")

        webhook_dlq = sqs.Queue(
            self, "WebhookDLQ",
            queue_name=f"{config['aws']['lambda']['function_name']}-dlq",
            retention_period=Duration.days(14),
            visibility_timeout=Duration.seconds(300)
        )

        job_queue_dlq = sqs.Queue(
            self, "JobQueueDLQ",
            queue_name=f"{config['aws']['lambda']['function_name']}-job-dlq",
            retention_period=Duration.days(14)
        )

        job_queue = sqs.Queue(
            self, "JobQueue",
            queue_name=f"{config['aws']['lambda']['function_name']}-jobs",
            visibility_timeout=Duration.seconds(config["aws"]["lambda"]["timeout_seconds"] * 6),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=3,
                queue=job_queue_dlq
            )
        )

        idempotency_table = dynamodb.Table(
            self, "IdempotencyTable",
            table_name=f"{config['aws']['lambda']['function_name']}-idempotency",
            partition_key=dynamodb.Attribute(
                name="request_id",
                type=dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="ttl",
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            point_in_time_recovery=True
        )

        webhook_router_lambda = lambda_.Function(
            self, "WebhookRouterHandler",
            function_name=config["aws"]["lambda"]["function_name"],
            runtime=lambda_.Runtime.PYTHON_3_14,
            handler="webhook_router.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(os.path.dirname(__file__), 'lambda')
            ),
            timeout=Duration.seconds(config["aws"]["lambda"]["timeout_seconds"]),
            memory_size=config["aws"]["lambda"]["memory_mb"],
            environment={
                "WEBHOOK_SECRET_NAME": webhook_secret_name,
                "API_BASE_URL": f"https://{config['fqdn']}",
                "IDEMPOTENCY_TABLE_NAME": idempotency_table.table_name,
                "JOB_QUEUE_URL": job_queue.queue_url,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="GitHub webhook router for GitHub self-hosted runners",
            dead_letter_queue=webhook_dlq,
            reserved_concurrent_executions=10
        )

        webhook_router_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["secretsmanager:GetSecretValue"],
                resources=[
                    f"arn:aws:secretsmanager:{config['aws']['region']}:"
                    f"{config['aws']['account_id']}:secret:{webhook_secret_name}-*"
                ]
            )
        )

        idempotency_table.grant_read_write_data(webhook_router_lambda)

        job_queue.grant_send_messages(webhook_router_lambda)

        webhook_router_lambda.add_event_source(
            lambda_events.SqsEventSource(
                job_queue,
                batch_size=1,
                max_batching_window=Duration.seconds(0)
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

        health_resource = runners_resource.add_resource("health")
        health_resource.add_method(
            "GET",
            apigw.LambdaIntegration(webhook_router_lambda)
        )

        webhook_config_lambda = lambda_.Function(
            self, "WebhookConfigHandler",
            function_name=f"{config['aws']['lambda']['function_name']}-config",
            runtime=lambda_.Runtime.PYTHON_3_14,
            handler="configure_webhook_handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(os.path.dirname(__file__), 'lambda')
            ),
            timeout=Duration.seconds(60),
            memory_size=256,
            environment={
                "WEBHOOK_SECRET_NAME": webhook_secret_name,
                "GITHUB_PAT_SECRET_NAME": github_pat_secret_name,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Configures GitHub webhook for self-hosted runners"
        )

        webhook_config_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:GetSecretValue",
                    "secretsmanager:CreateSecret"
                ],
                resources=[
                    f"arn:aws:secretsmanager:{config['aws']['region']}:"
                    f"{config['aws']['account_id']}:secret:{webhook_secret_name}-*",
                    f"arn:aws:secretsmanager:{config['aws']['region']}:"
                    f"{config['aws']['account_id']}:secret:"
                    f"{github_pat_secret_name}-*"
                ]
            )
        )

        webhook_provider = cr.Provider(
            self, "WebhookConfigProvider",
            on_event_handler=webhook_config_lambda,
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        _webhook_resource = CustomResource(
            self, "GitHubWebhook",
            service_token=webhook_provider.service_token,
            properties={
                "WebhookUrl": f"https://{config['fqdn']}/v1/runners",
                "Repository": config['github']['repository']
            }
        )

        error_alarm = cloudwatch.Alarm(
            self, "WebhookRouterErrorAlarm",
            alarm_name=f"{config['aws']['lambda']['function_name']}-errors",
            metric=webhook_router_lambda.metric_errors(
                period=Duration.minutes(5),
                statistic="Sum"
            ),
            evaluation_periods=1,
            threshold=5,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )

        throttle_alarm = cloudwatch.Alarm(
            self, "WebhookRouterThrottleAlarm",
            alarm_name=f"{config['aws']['lambda']['function_name']}-throttles",
            metric=webhook_router_lambda.metric_throttles(
                period=Duration.minutes(5),
                statistic="Sum"
            ),
            evaluation_periods=1,
            threshold=10,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )

        dlq_alarm = cloudwatch.Alarm(
            self, "WebhookDLQAlarm",
            alarm_name=f"{config['aws']['lambda']['function_name']}-dlq-messages",
            metric=webhook_dlq.metric_approximate_number_of_messages_visible(
                period=Duration.minutes(5),
                statistic="Maximum"
            ),
            evaluation_periods=1,
            threshold=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )

        job_queue_dlq_alarm = cloudwatch.Alarm(
            self, "JobQueueDLQAlarm",
            alarm_name=f"{config['aws']['lambda']['function_name']}-job-dlq-messages",
            metric=job_queue_dlq.metric_approximate_number_of_messages_visible(
                period=Duration.minutes(5),
                statistic="Maximum"
            ),
            evaluation_periods=1,
            threshold=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING
        )

        CfnOutput(
            self, "RunnersWebhookEndpoint",
            value=f"https://{config['fqdn']}/v1/runners",
            description="GitHub webhook endpoint for runner routing"
        )

        CfnOutput(
            self, "WebhookRouterLambdaName",
            value=webhook_router_lambda.function_name,
            description="Lambda function name for webhook router"
        )
