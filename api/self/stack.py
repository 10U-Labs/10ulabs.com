import os
from typing import Dict, Any

from aws_cdk import (
    Stack,
    CfnOutput,
    Duration,
    RemovalPolicy,
    Fn,
    Tags,
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
)
from constructs import Construct


class ApiStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        parent_domain = config["domain_names"]["parent"]
        subdomain_name = config["domain_names"]["subdomain"]
        normalized_parent_domain = parent_domain.replace('.', '-')

        max_azs = config["aws"]["vpc"].get("max_azs", 99)
        self.vpc = ec2.Vpc(
            self, "RunnerVpc",
            vpc_name=config["naming"]["vpc_name"],
            ip_addresses=ec2.IpAddresses.cidr(config["aws"]["vpc"]["cidr"]),
            max_azs=max_azs,
            nat_gateways=config["aws"]["vpc"]["nat_gateways"],
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=config["aws"]["vpc"]["subnet_configuration"]["public_subnet_cidr_mask"],
                    map_public_ip_on_launch=True
                )
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        Tags.of(self.vpc).add("Purpose", "10ulabs-api-and-runners")

        self.ecr_repository = ecr.Repository(
            self, "RunnerEcrRepository",
            repository_name=config["aws"]["fargate_runners"]["ecr_repository"],
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
            cluster_name=config["naming"]["cluster_name"],
            vpc=self.vpc,
            container_insights=True
        )

        github_token_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "GitHubToken",
            secret_name=config["naming"]["github_token_secret_name"]
        )

        self.webhook_secret = secretsmanager.Secret(
            self, "WebhookSecret",
            secret_name=config["naming"]["webhook_secret_name"],
            description="GitHub webhook secret for signature verification",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                exclude_punctuation=True,
                password_length=32
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

        self.task_definition = ecs.FargateTaskDefinition(
            self, "RunnerTaskDefinition",
            family=config["naming"]["task_family"],
            cpu=int(config["aws"]["fargate_runners"]["cpu"]),
            memory_limit_mib=int(config["aws"]["fargate_runners"]["memory"]),
        )

        self.task_definition.add_container(
            "runner",
            container_name=config["naming"]["container_name"],
            image=ecs.ContainerImage.from_ecr_repository(
                self.ecr_repository,
                tag="latest"
            ),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix=config["naming"]["log_stream_prefix"],
                log_retention=logs.RetentionDays.ONE_WEEK
            ),
            secrets={
                "GITHUB_TOKEN": ecs.Secret.from_secrets_manager(github_token_secret)
            },
            environment={
                "GITHUB_REPO": config["github"]["repo"],
                "RUNNER_LABELS": ",".join(config["aws"]["fargate_runners"]["runner_labels"]),
                "EPHEMERAL": "true",
                "RUNNER_NAME_PREFIX": "fargate_runner"
            }
        )

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

        runner_sg = ec2.SecurityGroup(
            self, "SelfHostedRunnerSecurityGroup",
            vpc=self.vpc,
            description="Security group for GitHub self-hosted runner Fargate tasks",
            allow_all_outbound=True
        )

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

        webhook_router = lambda_.Function(
            self, "WebhookRouter",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="webhook_runner_launcher.lambda_handler",
            code=lambda_.Code.from_asset("api/collections/runners"),
            timeout=Duration.seconds(config["lambda"]["timeout_seconds"]),
            memory_size=config["lambda"]["memory_mb"],
            environment={
                "ECS_CLUSTER": self.cluster.cluster_name,
                "TASK_DEFINITION": self.task_definition.task_definition_arn,
                "SUBNETS": ",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
                "SECURITY_GROUPS": runner_sg.security_group_id,
                "WEBHOOK_SECRET": self.webhook_secret.secret_name,
                "GITHUB_TOKEN_SECRET_NAME": config["naming"]["github_token_secret_name"],
                "GITHUB_REPO": config["github"]["repo"],
                "RUNNER_LABELS": ",".join(config["aws"]["fargate_runners"]["runner_labels"]),
                "EC2_AMI_ID": "ami-placeholder",
                "EC2_INSTANCE_TYPES": ",".join(config["aws"]["ec2_runners"]["spot_instance_types"]),
                "EC2_IAM_INSTANCE_PROFILE": "GitHubSelfHostedRunnerInstanceProfile",
                "API_ENDPOINT": f"https://{subdomain_name}"
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Routes GitHub webhook events to appropriate runner launcher"
        )

        webhook_router.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ecs:RunTask"],
                resources=[self.task_definition.task_definition_arn],
                conditions={
                    "ArnEquals": {
                        "ecs:cluster": self.cluster.cluster_arn
                    }
                }
            )
        )

        task_role = self.task_definition.task_role
        execution_role = self.task_definition.execution_role
        assert task_role is not None
        assert execution_role is not None

        webhook_router.add_to_role_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                resources=[
                    task_role.role_arn,
                    execution_role.role_arn
                ],
                conditions={
                    "StringLike": {
                        "iam:PassedToService": "ecs-tasks.amazonaws.com"
                    }
                }
            )
        )

        webhook_router.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:RunInstances",
                    "ec2:TerminateInstances",
                    "ec2:CreateTags",
                    "ec2:DescribeInstances",
                    "ec2:DescribeImages"
                ],
                resources=["*"]
            )
        )

        webhook_router.add_to_role_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                resources=["arn:aws:iam::*:role/GitHubSelfHostedRunnerEC2Role"],
                conditions={
                    "StringEquals": {
                        "iam:PassedToService": "ec2.amazonaws.com"
                    }
                }
            )
        )

        self.webhook_secret.grant_read(webhook_router)
        github_token_secret.grant_read(webhook_router)

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

        api.root.add_resource("health").add_method("GET", apigw.LambdaIntegration(api_handler))

        v1 = api.root.add_resource("v1")

        v1.add_resource("echo").add_method(
            "POST", apigw.LambdaIntegration(api_handler)
        )

        v1.add_resource("runners").add_method(
            "POST", apigw.LambdaIntegration(webhook_router)
        )

        v1.add_resource("ec2-runner").add_method(
            "POST", apigw.LambdaIntegration(webhook_router)
        )

        v1.add_resource("docker-runner").add_method(
            "POST", apigw.LambdaIntegration(webhook_router)
        )

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

        CfnOutput(
            self, "VpcId",
            value=self.vpc.vpc_id,
            description="VPC ID for API and GitHub self-hosted runners"
        )

        CfnOutput(
            self, "EcrRepositoryUri",
            value=self.ecr_repository.repository_uri,
            description="ECR repository URI for self-hosted runner Docker images"
        )

        CfnOutput(
            self, "EcrRepositoryName",
            value=self.ecr_repository.repository_name,
            description="ECR repository name for self-hosted runners"
        )

        CfnOutput(
            self, "ClusterName",
            value=self.cluster.cluster_name,
            description="ECS cluster name for GitHub self-hosted runners"
        )

        CfnOutput(
            self, "WebhookUrl",
            value=f"https://{subdomain_name}/v1/runners",
            description="GitHub webhook URL - configure this in your repository settings"
        )

        CfnOutput(
            self, "WebhookSecretArn",
            value=self.webhook_secret.secret_arn,
            description="ARN of the webhook secret - retrieve value to configure GitHub webhook"
        )

        CfnOutput(
            self, "EC2RunnerEndpoint",
            value=f"https://{subdomain_name}/v1/ec2-runner",
            description="EC2 Spot runner launcher endpoint"
        )

        CfnOutput(
            self, "DockerRunnerEndpoint",
            value=f"https://{subdomain_name}/v1/docker-runner",
            description="Fargate Spot runner launcher endpoint"
        )
