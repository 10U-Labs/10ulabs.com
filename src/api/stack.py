import os
from typing import Dict, Any

from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    RemovalPolicy,
    Fn,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_apigateway as apigw,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_certificatemanager as acm,
)
from constructs import Construct


class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        parent_domain = config["parent_domain"]
        subdomain_name = config["subdomain_name"]
        normalized_parent_domain = parent_domain.replace('.', '-')

        parent_zone = route53.HostedZone.from_hosted_zone_attributes(
            self, "ParentHostedZone",
            hosted_zone_id=Fn.import_value(f"{normalized_parent_domain}-HostedZoneId"),
            zone_name=parent_domain
        )

        certificate = acm.Certificate(
            self, "ApiCertificate",
            domain_name=subdomain_name,
            validation=acm.CertificateValidation.from_dns(parent_zone)
        )

        lambda_dir = os.path.join(os.path.dirname(__file__), "lambda")

        api_handler = lambda_.Function(
            self, "ApiHandler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=lambda_.Code.from_asset(lambda_dir),
            timeout=Duration.seconds(30),
            description="API handler for 10U Labs API",
            log_retention=logs.RetentionDays.ONE_WEEK
        )

        api_log_group = logs.LogGroup(
            self, "ApiGatewayAccessLogs",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )

        api = apigw.LambdaRestApi(
            self, "TenULabsApi",
            handler=api_handler,
            proxy=False,
            domain_name=apigw.DomainNameOptions(
                domain_name=subdomain_name,
                certificate=certificate
            ),
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                logging_level=apigw.MethodLoggingLevel.INFO,
                access_log_destination=apigw.LogGroupLogDestination(api_log_group),
                access_log_format=apigw.AccessLogFormat.clf()
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS
            )
        )

        health = api.root.add_resource("health")
        health.add_method("GET", apigw.LambdaIntegration(api_handler))

        v1 = api.root.add_resource("v1")
        echo = v1.add_resource("echo")
        echo.add_method("POST", apigw.LambdaIntegration(api_handler))

        route53.ARecord(
            self, "ApiAliasRecord",
            zone=parent_zone,
            record_name=subdomain_name,
            target=route53.RecordTarget.from_alias(targets.ApiGateway(api))
        )

        CfnOutput(
            self, "ApiUrl",
            value=api.url,
            description=f"API Gateway URL for {subdomain_name}"
        )

        CfnOutput(
            self, "ApiDomainName",
            value=subdomain_name,
            description="Custom domain name for API"
        )

        CfnOutput(
            self, "ApiEndpoint",
            value=f"https://{subdomain_name}",
            description="API endpoint URL"
        )
