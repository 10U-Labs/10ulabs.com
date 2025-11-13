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

        api_log_group = logs.LogGroup(
            self, "ApiGatewayAccessLogs",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY
        )

        self.api = apigw.LambdaRestApi(
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

        self.api.root.add_resource("health").add_method("GET", apigw.LambdaIntegration(api_handler))

        self.v1 = self.api.root.add_resource("v1")

        self.v1.add_resource("echo").add_method(
            "POST", apigw.LambdaIntegration(api_handler)
        )

        route53.ARecord(
            self, "ApiAliasRecord",
            zone=parent_zone,
            record_name=subdomain_name,
            target=route53.RecordTarget.from_alias(targets.ApiGateway(self.api))
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
            self, "ApiGatewayV1ResourceId",
            value=self.v1.resource_id,
            description="API Gateway /v1 resource ID for adding versioned routes",
            export_name="TenULabsApi-V1ResourceId"
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
            value=self.task_definition.execution_role.role_arn,
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
            value=config["naming"]["github_token_secret_name"],
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
