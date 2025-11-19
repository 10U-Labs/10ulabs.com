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
    aws_events as events,
    aws_events_targets as targets,
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
            tracing=lambda_.Tracing.ACTIVE
        )

        webhook_router_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[
                    f"arn:aws:ssm:{config['aws']['region']}:"
                    f"{config['aws']['account_id']}:parameter{webhook_secret_name}"
                ]
            )
        )

        idempotency_table.grant_read_write_data(webhook_router_lambda)

        job_queue.grant_send_messages(webhook_router_lambda)

        webhook_router_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["cloudwatch:PutMetricData"],
                resources=["*"]
            )
        )

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
                    "ssm:GetParameter",
                    "ssm:PutParameter"
                ],
                resources=[
                    f"arn:aws:ssm:{config['aws']['region']}:"
                    f"{config['aws']['account_id']}:parameter{webhook_secret_name}",
                    f"arn:aws:ssm:{config['aws']['region']}:"
                    f"{config['aws']['account_id']}:parameter{github_pat_secret_name}"
                ]
            )
        )

        dlq_reprocessor_lambda = lambda_.Function(
            self, "DLQReprocessor",
            function_name=f"{config['aws']['lambda']['function_name']}-dlq-reprocessor",
            runtime=lambda_.Runtime.PYTHON_3_14,
            handler="dlq_reprocessor.handler",
            code=lambda_.Code.from_asset(
                os.path.join(os.path.dirname(__file__), 'lambda')
            ),
            timeout=Duration.seconds(300),
            memory_size=256,
            environment={
                "WEBHOOK_DLQ_URL": webhook_dlq.queue_url,
                "JOB_DLQ_URL": job_queue_dlq.queue_url,
                "JOB_QUEUE_URL": job_queue.queue_url,
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Reprocesses messages from DLQs for self-healing",
            tracing=lambda_.Tracing.ACTIVE
        )

        dlq_reprocessor_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes"
                ],
                resources=[webhook_dlq.queue_arn, job_queue_dlq.queue_arn]
            )
        )

        dlq_reprocessor_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["sqs:SendMessage"],
                resources=[job_queue.queue_arn]
            )
        )

        dlq_reprocessor_rule = events.Rule(
            self, "DLQReprocessorSchedule",
            schedule=events.Schedule.rate(Duration.minutes(15)),
            description="Triggers DLQ reprocessor every 15 minutes"
        )

        dlq_reprocessor_rule.add_target(targets.LambdaFunction(dlq_reprocessor_lambda))

        circuit_breaker_remediation_lambda = lambda_.Function(
            self, "CircuitBreakerRemediation",
            function_name=f"{config['aws']['lambda']['function_name']}-cb-remediation",
            runtime=lambda_.Runtime.PYTHON_3_14,
            handler="circuit_breaker_remediation.handler",
            code=lambda_.Code.from_asset(
                os.path.join(os.path.dirname(__file__), 'lambda')
            ),
            timeout=Duration.seconds(60),
            memory_size=256,
            environment={
                "WEBHOOK_FUNCTION_NAME": config['aws']['lambda']['function_name'],
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Monitors and remediates circuit breaker state",
            tracing=lambda_.Tracing.ACTIVE
        )

        circuit_breaker_remediation_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["lambda:InvokeFunction"],
                resources=[webhook_router_lambda.function_arn]
            )
        )

        circuit_breaker_remediation_rule = events.Rule(
            self, "CircuitBreakerRemediationSchedule",
            schedule=events.Schedule.rate(Duration.minutes(5)),
            description="Monitors circuit breaker health every 5 minutes"
        )

        circuit_breaker_remediation_rule.add_target(
            targets.LambdaFunction(circuit_breaker_remediation_lambda)
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

        alarm_topic = sns.Topic(
            self, "AlarmTopic",
            topic_name=f"{config['aws']['lambda']['function_name']}-alarms",
            display_name="Webhook Router Alarms"
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

        error_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))
        throttle_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))
        dlq_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))
        job_queue_dlq_alarm.add_alarm_action(cw_actions.SnsAction(alarm_topic))

        dashboard = cloudwatch.Dashboard(
            self, "WebhookRouterDashboard",
            dashboard_name=f"{config['aws']['lambda']['function_name']}-dashboard"
        )

        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Performance",
                left=[
                    webhook_router_lambda.metric_duration(statistic="Average"),
                    webhook_router_lambda.metric_duration(statistic="Maximum")
                ],
                right=[
                    webhook_router_lambda.metric_invocations(statistic="Sum")
                ]
            ),
            cloudwatch.GraphWidget(
                title="Lambda Errors & Throttles",
                left=[
                    webhook_router_lambda.metric_errors(statistic="Sum"),
                    webhook_router_lambda.metric_throttles(statistic="Sum")
                ]
            )
        )

        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Circuit Breaker State",
                left=[
                    cloudwatch.Metric(
                        namespace="WebhookRouter",
                        metric_name="CircuitBreakerState",
                        statistic="Maximum"
                    )
                ]
            ),
            cloudwatch.GraphWidget(
                title="Processing Time",
                left=[
                    cloudwatch.Metric(
                        namespace="WebhookRouter",
                        metric_name="ProcessingTime",
                        statistic="Average",
                        unit=cloudwatch.Unit.MILLISECONDS
                    ),
                    cloudwatch.Metric(
                        namespace="WebhookRouter",
                        metric_name="ProcessingTime",
                        statistic="Maximum",
                        unit=cloudwatch.Unit.MILLISECONDS
                    )
                ]
            )
        )

        dashboard.add_widgets(
            cloudwatch.GraphWidget(
                title="Queue Depth",
                left=[
                    cloudwatch.Metric(
                        namespace="WebhookRouter",
                        metric_name="QueueDepth",
                        statistic="Average"
                    ),
                    job_queue.metric_approximate_number_of_messages_visible(statistic="Maximum")
                ]
            ),
            cloudwatch.GraphWidget(
                title="DLQ Messages",
                left=[
                    webhook_dlq.metric_approximate_number_of_messages_visible(statistic="Maximum"),
                    job_queue_dlq.metric_approximate_number_of_messages_visible(statistic="Maximum")
                ]
            )
        )

        dashboard.add_widgets(
            cloudwatch.AlarmStatusWidget(
                title="Alarms",
                alarms=[error_alarm, throttle_alarm, dlq_alarm, job_queue_dlq_alarm]
            )
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

        CfnOutput(
            self, "AlarmTopicArn",
            value=alarm_topic.topic_arn,
            description="SNS topic ARN for CloudWatch alarm notifications"
        )

        CfnOutput(
            self, "DashboardURL",
            value=f"https://console.aws.amazon.com/cloudwatch/home?region={config['aws']['region']}#dashboards:name={config['aws']['lambda']['function_name']}-dashboard",
            description="CloudWatch Dashboard URL"
        )
