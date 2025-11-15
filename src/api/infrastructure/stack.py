import os
import hashlib
from typing import Dict, Any

import yaml

from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    RemovalPolicy,
    Fn,
    Tags,
    BundlingOptions,
    DockerImage,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_apigateway as apigw,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_certificatemanager as acm,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_iam as iam,
    aws_secretsmanager as secretsmanager,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_wafv2 as wafv2,
)
from aws_cdk.aws_cloudfront import OriginProtocolPolicy
from constructs import Construct


class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        self.config = config

        self._create_vpc()
        self._create_ecr_and_ecs()
        secrets_and_security = self._create_secrets_and_security()
        self._create_fargate_task(secrets_and_security[0])
        ec2_runner_role = self._create_ec2_runner_role()

        parent_domain = config["domain_names"]["parent"]
        subdomain = config["domain_names"]["subdomain"]
        cert_info = self._create_certificate(parent_domain, subdomain, parent_domain.replace('.', '-'))

        self._create_api_gateway(subdomain, cert_info[1], self._create_lambda_functions())
        cf_dist = self._create_cloudfront(subdomain, cert_info[1], self._create_waf())
        self._create_dns_and_outputs(cert_info[0], subdomain, cf_dist, (secrets_and_security[1], ec2_runner_role))

    def _create_vpc(self):
        max_azs = self.config["aws"]["vpc"].get("max_azs", 99)
        self.vpc = ec2.Vpc(
            self, "RunnerVpc",
            vpc_name=self.config["naming"]["vpc_name"],
            ip_addresses=ec2.IpAddresses.cidr(self.config["aws"]["vpc"]["cidr"]),
            max_azs=max_azs,
            nat_gateways=self.config["aws"]["vpc"]["nat_gateways"],
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=self.config["aws"]["vpc"]["subnet_configuration"]["public_subnet_cidr_mask"],
                    map_public_ip_on_launch=True
                )
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        Tags.of(self.vpc).add("Purpose", "10ulabs-api-and-runners")

    def _create_ecr_and_ecs(self):
        self.ecr_repository = ecr.Repository(
            self, "RunnerEcrRepository",
            repository_name=self.config["aws"]["fargate_runners"]["ecr_repository"],
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True,
            image_scan_on_push=True,
            lifecycle_rules=[
                ecr.LifecycleRule(
                    description="Keep only last 3 images",
                    max_image_count=3,
                    rule_priority=1
                )
            ]
        )
        self.cluster = ecs.Cluster(
            self, "RunnerCluster",
            cluster_name=self.config["naming"]["cluster_name"],
            vpc=self.vpc,
            container_insights=True
        )

    def _create_secrets_and_security(self):
        github_token_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "GitHubToken",
            secret_name=self.config["naming"]["github_token_secret_name"]
        )
        self.webhook_secret = secretsmanager.Secret(
            self, "WebhookSecret",
            secret_name=self.config["naming"]["webhook_secret_name"],
            description="GitHub webhook secret for signature verification",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                exclude_punctuation=True,
                password_length=32
            ),
            removal_policy=RemovalPolicy.DESTROY
        )
        runner_sg = ec2.SecurityGroup(
            self, "SelfHostedRunnerSecurityGroup",
            vpc=self.vpc,
            description="Security group for GitHub self-hosted runner Fargate tasks",
            allow_all_outbound=True
        )
        return github_token_secret, runner_sg

    def _create_fargate_task(self, github_token_secret):
        self.task_definition = ecs.FargateTaskDefinition(
            self, "RunnerTaskDefinition",
            family=self.config["naming"]["task_family"],
            cpu=int(self.config["aws"]["fargate_runners"]["cpu"]),
            memory_limit_mib=int(self.config["aws"]["fargate_runners"]["memory"]),
        )
        self.task_definition.add_container(
            "runner",
            container_name=self.config["naming"]["container_name"],
            image=ecs.ContainerImage.from_ecr_repository(
                self.ecr_repository,
                tag="latest"
            ),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix=self.config["naming"]["log_stream_prefix"],
                log_retention=logs.RetentionDays.ONE_WEEK
            ),
            secrets={
                "GITHUB_TOKEN": ecs.Secret.from_secrets_manager(github_token_secret)
            },
            environment={
                "GITHUB_REPO": self.config["github"]["repo"],
                "RUNNER_LABELS": ",".join(self.config["aws"]["fargate_runners"]["runner_labels"]),
                "EPHEMERAL": "true",
                "RUNNER_NAME_PREFIX": "fargate_runner"
            }
        )

    def _create_ec2_runner_role(self):
        ec2_runner_role = iam.Role(
            self, "EC2SelfHostedRunnerRole",
            role_name="GitHubSelfHostedRunnerEC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
            ],
            inline_policies={
                "ECRAccess": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["ecr:*"],
                            resources=["*"]
                        )
                    ]
                ),
                "SelfTerminate": iam.PolicyDocument(
                    statements=[
                        iam.PolicyStatement(
                            effect=iam.Effect.ALLOW,
                            actions=["ec2:TerminateInstances"],
                            resources=["*"],
                            conditions={
                                "StringEquals": {
                                    "ec2:ResourceTag/ManagedBy": "webhook-handler"
                                }
                            }
                        )
                    ]
                )
            }
        )
        ec2_instance_profile = iam.CfnInstanceProfile(
            self, "EC2SelfHostedRunnerInstanceProfile",
            instance_profile_name="GitHubSelfHostedRunnerInstanceProfile",
            roles=[ec2_runner_role.role_name]
        )
        ec2_instance_profile.node.add_dependency(ec2_runner_role)
        return ec2_runner_role

    def _create_certificate(self, parent_domain, subdomain_name, normalized_parent_domain):
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
        return parent_zone, certificate

    def _create_lambda_functions(self):
        api_dir = os.path.join(os.path.dirname(__file__), "..")
        health_endpoint_dir = os.path.join(os.path.dirname(__file__), "..", "endpoints", "health")
        echo_endpoint_dir = os.path.join(os.path.dirname(__file__), "..", "endpoints", "v1", "echo")
        docs_handler = lambda_.Function(
            self, "DocsHandler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="endpoints/root/handler.handler",
            code=lambda_.Code.from_asset(
                api_dir,
                bundling=BundlingOptions(
                    image=DockerImage.from_registry("public.ecr.aws/sam/build-python3.11"),
                    command=[
                        "bash", "-c",
                        "pip install -r endpoints/root/requirements.txt -t /asset-output && "
                        "cp -r endpoints /asset-output/ && "
                        "cp openapi.yaml /asset-output/"
                    ]
                )
            ),
            timeout=Duration.seconds(10),
            description="Serves OpenAPI documentation at api.10ulabs.com/",
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        health_handler = lambda_.Function(
            self, "HealthHandler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=lambda_.Code.from_asset(health_endpoint_dir),
            timeout=Duration.seconds(10),
            description="Health check endpoint for API",
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        echo_handler = lambda_.Function(
            self, "EchoHandler",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.handler",
            code=lambda_.Code.from_asset(echo_endpoint_dir),
            timeout=Duration.seconds(10),
            description="Echo endpoint for testing",
            log_retention=logs.RetentionDays.ONE_WEEK
        )
        return docs_handler, health_handler, echo_handler

    def _create_api_gateway(self, subdomain_name, certificate, handlers):
        docs_handler, health_handler, echo_handler = handlers
        openapi_spec_path = os.path.join(os.path.dirname(__file__), "..", "openapi.yaml")
        with open(openapi_spec_path, 'r', encoding='utf-8') as f:
            openapi_spec = yaml.safe_load(f)

        openapi_spec_str = yaml.dump(openapi_spec)
        openapi_spec_str = openapi_spec_str.replace(
            '${DocsHandlerArn}',
            f'arn:aws:apigateway:{self.config["aws"]["region"]}:lambda:path/2015-03-31/functions/{docs_handler.function_arn}/invocations'
        )
        openapi_spec_str = openapi_spec_str.replace(
            '${HealthHandlerArn}',
            f'arn:aws:apigateway:{self.config["aws"]["region"]}:lambda:path/2015-03-31/functions/{health_handler.function_arn}/invocations'
        )
        openapi_spec_str = openapi_spec_str.replace(
            '${EchoHandlerArn}',
            f'arn:aws:apigateway:{self.config["aws"]["region"]}:lambda:path/2015-03-31/functions/{echo_handler.function_arn}/invocations'
        )

        spec_hash = hashlib.md5(openapi_spec_str.encode('utf-8')).hexdigest()[:8]

        api_log_group = logs.LogGroup(
            self, "ApiGatewayAccessLogs",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )
        self.api = apigw.SpecRestApi(
            self, "TenULabsApi",
            api_definition=apigw.ApiDefinition.from_inline(yaml.safe_load(openapi_spec_str)),
            domain_name=apigw.DomainNameOptions(
                domain_name=subdomain_name,
                certificate=certificate
            ),
            deploy=False
        )

        deployment = apigw.Deployment(
            self, f"ApiDeployment{spec_hash}",
            api=self.api,
            description=f"Deployment for spec hash {spec_hash}"
        )

        stage = apigw.Stage(
            self, "ProdStage",
            deployment=deployment,
            stage_name="prod",
            logging_level=apigw.MethodLoggingLevel.INFO,
            access_log_destination=apigw.LogGroupLogDestination(api_log_group),
            access_log_format=apigw.AccessLogFormat.clf()
        )

        stage.node.add_dependency(deployment)

        self.api.deployment_stage = stage
        docs_handler.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.config['aws']['region']}:{self.config['aws']['account_id']}:{self.api.rest_api_id}/*/*/"
        )
        health_handler.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.config['aws']['region']}:{self.config['aws']['account_id']}:{self.api.rest_api_id}/*/GET/health"
        )
        echo_handler.add_permission(
            "ApiGatewayInvoke",
            principal=iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:aws:execute-api:{self.config['aws']['region']}:{self.config['aws']['account_id']}:{self.api.rest_api_id}/*/POST/v1/echo"
        )

    def _create_waf(self):
        return wafv2.CfnWebACL(
            self, "ApiWafWebAcl",
            scope="CLOUDFRONT",
            default_action=wafv2.CfnWebACL.DefaultActionProperty(
                allow={}
            ),
            visibility_config=wafv2.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name="ApiWafMetrics",
                sampled_requests_enabled=True
            ),
            rules=[]
        )

    def _create_cloudfront(self, subdomain_name, certificate, web_acl):
        cf_cache_policy = cloudfront.CachePolicy(
            self, "ApiDocsCachePolicy",
            cache_policy_name="ApiDocsCachePolicy",
            default_ttl=Duration.hours(24),
            min_ttl=Duration.minutes(1),
            max_ttl=Duration.days(365),
            cookie_behavior=cloudfront.CacheCookieBehavior.none(),
            header_behavior=cloudfront.CacheHeaderBehavior.none(),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.none(),
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True
        )
        return cloudfront.Distribution(
            self, "ApiDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.HttpOrigin(
                    subdomain_name,
                    protocol_policy=OriginProtocolPolicy.HTTPS_ONLY
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                cache_policy=cf_cache_policy,
                origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER
            ),
            additional_behaviors={
                "/health": cloudfront.BehaviorOptions(
                    origin=origins.HttpOrigin(
                        subdomain_name,
                        protocol_policy=OriginProtocolPolicy.HTTPS_ONLY
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER
                ),
                "/v1/*": cloudfront.BehaviorOptions(
                    origin=origins.HttpOrigin(
                        subdomain_name,
                        protocol_policy=OriginProtocolPolicy.HTTPS_ONLY
                    ),
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER
                )
            },
            domain_names=[subdomain_name],
            certificate=certificate,
            web_acl_id=web_acl.attr_arn
        )

    def _create_dns_and_outputs(self, parent_zone, subdomain_name, cf_distribution, resources):
        runner_sg, ec2_runner_role = resources
        route53.ARecord(
            self, "ApiAliasRecord",
            zone=parent_zone,
            record_name=subdomain_name,
            target=route53.RecordTarget.from_alias(targets.CloudFrontTarget(cf_distribution))
        )

        CfnOutput(
            self, "ApiUrl",
            value=self.api.url,
            description=f"API Gateway URL for {subdomain_name}",
            export_name="TenULabsApi-Url"
        )

        CfnOutput(
            self, "ApiDomainName",
            value=subdomain_name,
            description="Custom domain name for API",
            export_name="TenULabsApi-DomainName"
        )

        CfnOutput(
            self, "ApiEndpoint",
            value=f"https://{subdomain_name}",
            description="API endpoint URL",
            export_name="TenULabsApi-Endpoint"
        )

        CfnOutput(
            self, "ApiGatewayRestApiId",
            value=self.api.rest_api_id,
            description="API Gateway REST API ID for route additions",
            export_name="TenULabsApi-RestApiId"
        )

        CfnOutput(
            self, "ApiGatewayRootResourceId",
            value=self.api.rest_api_root_resource_id,
            description="API Gateway root resource ID",
            export_name="TenULabsApi-RootResourceId"
        )

        CfnOutput(
            self, "VpcId",
            value=self.vpc.vpc_id,
            description="VPC ID for API and GitHub self-hosted runners",
            export_name="TenULabsApi-VpcId"
        )

        CfnOutput(
            self, "VpcPublicSubnetIds",
            value=",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
            description="Comma-separated list of public subnet IDs",
            export_name="TenULabsApi-PublicSubnetIds"
        )

        CfnOutput(
            self, "RunnerSecurityGroupId",
            value=runner_sg.security_group_id,
            description="Security group ID for runners",
            export_name="TenULabsApi-RunnerSecurityGroupId"
        )

        CfnOutput(
            self, "EcrRepositoryUri",
            value=self.ecr_repository.repository_uri,
            description="ECR repository URI for self-hosted runner Docker images",
            export_name="TenULabsApi-EcrRepositoryUri"
        )

        CfnOutput(
            self, "EcrRepositoryName",
            value=self.ecr_repository.repository_name,
            description="ECR repository name for self-hosted runners",
            export_name="TenULabsApi-EcrRepositoryName"
        )

        CfnOutput(
            self, "ClusterName",
            value=self.cluster.cluster_name,
            description="ECS cluster name for GitHub self-hosted runners",
            export_name="TenULabsApi-ClusterName"
        )

        CfnOutput(
            self, "ClusterArn",
            value=self.cluster.cluster_arn,
            description="ECS cluster ARN for GitHub self-hosted runners",
            export_name="TenULabsApi-ClusterArn"
        )

        CfnOutput(
            self, "TaskDefinitionArn",
            value=self.task_definition.task_definition_arn,
            description="Fargate task definition ARN for runners",
            export_name="TenULabsApi-TaskDefinitionArn"
        )

        CfnOutput(
            self, "TaskRoleArn",
            value=self.task_definition.task_role.role_arn,
            description="Task role ARN for Fargate runners",
            export_name="TenULabsApi-TaskRoleArn"
        )

        CfnOutput(
            self, "ExecutionRoleArn",
            value=self.task_definition.execution_role.role_arn if self.task_definition.execution_role else "",
            description="Execution role ARN for Fargate runners",
            export_name="TenULabsApi-ExecutionRoleArn"
        )

        CfnOutput(
            self, "WebhookSecretName",
            value=self.webhook_secret.secret_name,
            description="Webhook secret name in Secrets Manager",
            export_name="TenULabsApi-WebhookSecretName"
        )

        CfnOutput(
            self, "WebhookSecretArn",
            value=self.webhook_secret.secret_arn,
            description="ARN of the webhook secret",
            export_name="TenULabsApi-WebhookSecretArn"
        )

        CfnOutput(
            self, "GitHubTokenSecretName",
            value=self.config["naming"]["github_token_secret_name"],
            description="GitHub token secret name in Secrets Manager",
            export_name="TenULabsApi-GitHubTokenSecretName"
        )

        CfnOutput(
            self, "EC2RunnerRoleName",
            value=ec2_runner_role.role_name,
            description="EC2 runner IAM role name",
            export_name="TenULabsApi-EC2RunnerRoleName"
        )

        CfnOutput(
            self, "EC2InstanceProfileName",
            value="GitHubSelfHostedRunnerInstanceProfile",
            description="EC2 instance profile name for runners",
            export_name="TenULabsApi-EC2InstanceProfileName"
        )
