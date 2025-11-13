"""GitHub Self-Hosted Runners Infrastructure Stack - Merged VPC + Webhook + ECR"""
from typing import Dict, Any
from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    Tags,
    CfnOutput,
    aws_ec2 as ec2,
    aws_ecr as ecr,
    aws_ecs as ecs,
    aws_lambda as lambda_,
    aws_apigatewayv2 as apigw,
    aws_apigatewayv2_integrations as integrations,
    aws_iam as iam,
    aws_logs as logs,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct
class GitHubSelfHostedRunnersStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, config: Dict[str, Any], **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        max_azs = config["vpc"].get("max_azs", 99)
        self.vpc = ec2.Vpc(
            self, "RunnerVpc",
            vpc_name=config["naming"]["vpc_name"],
            ip_addresses=ec2.IpAddresses.cidr(config["vpc"]["cidr"]),
            max_azs=max_azs,
            nat_gateways=config["vpc"]["nat_gateways"],
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=config["vpc"]["subnet_configuration"]["public_subnet_cidr_mask"],
                    map_public_ip_on_launch=True
                )
            ],
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
        Tags.of(self.vpc).add("Purpose", "github-self-hosted-runners")
        self.ecr_repository = ecr.Repository(
            self, "RunnerEcrRepository",
            repository_name=config["fargate_runners"]["ecr_repository"],
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
            cpu=int(config["fargate_runners"]["cpu"]),
            memory_limit_mib=int(config["fargate_runners"]["memory"]),
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
                "RUNNER_LABELS": ",".join(config["fargate_runners"]["runner_labels"]),
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
        self.webhook_lambda = lambda_.Function(
            self, "WebhookHandler",
            function_name=config["naming"]["lambda_function_name"],
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="webhook_runner_launcher.lambda_handler",
            code=lambda_.Code.from_asset("src/api/collections/ecr_for_runners"),
            timeout=Duration.seconds(config["lambda"]["timeout_seconds"]),
            memory_size=config["lambda"]["memory_mb"],
            environment={
                "ECS_CLUSTER": self.cluster.cluster_name,
                "TASK_DEFINITION": self.task_definition.task_definition_arn,
                "SUBNETS": ",".join([subnet.subnet_id for subnet in self.vpc.public_subnets]),
                "SECURITY_GROUPS": runner_sg.security_group_id,
                "WEBHOOK_SECRET": self.webhook_secret.secret_name,
                "GITHUB_REPO": config["github"]["repo"],
                "RUNNER_LABELS": ",".join(config["fargate_runners"]["runner_labels"]),
                "EC2_AMI_ID": "ami-placeholder",
                "EC2_INSTANCE_TYPES": ",".join(
                    config.get("docker_builder", {}).get("spot_instance_types", ["t4g.large"])
                ),
                "EC2_IAM_INSTANCE_PROFILE": "GitHubSelfHostedRunnerInstanceProfile"
            },
            log_retention=logs.RetentionDays.ONE_WEEK,
            description="Handles GitHub webhook events and launches ephemeral self-hosted runners"
        )
        self.webhook_lambda.add_to_role_policy(
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
        assert task_role is not None, "Task role should be auto-created"
        assert execution_role is not None, "Execution role should be auto-created"
        self.webhook_lambda.add_to_role_policy(
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
        self.webhook_lambda.add_to_role_policy(
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
        self.webhook_lambda.add_to_role_policy(
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
        self.webhook_secret.grant_read(self.webhook_lambda)
        github_token_secret.grant_read(self.webhook_lambda)
        webhook_version = self.webhook_lambda.current_version
        webhook_alias = lambda_.Alias(
            self, "WebhookProdAlias",
            alias_name="prod",
            version=webhook_version,
            description="Production alias for webhook handler"
        )
        self.http_api = apigw.HttpApi(
            self, "WebhookApi",
            api_name=config["naming"]["api_gateway_name"],
            description="GitHub webhook receiver for ephemeral self-hosted runners",
            cors_preflight=apigw.CorsPreflightOptions(
                allow_origins=["https://github.com"],
                allow_methods=[apigw.CorsHttpMethod.POST],
                allow_headers=["Content-Type", "X-GitHub-Event", "X-Hub-Signature-256"]
            )
        )
        self.http_api.add_routes(
            path="/webhook",
            methods=[apigw.HttpMethod.POST],
            integration=integrations.HttpLambdaIntegration(
                "WebhookIntegration",
                webhook_alias
            )
        )
        CfnOutput(
            self, "VpcId",
            value=self.vpc.vpc_id,
            description="VPC ID for GitHub self-hosted runners"
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
            value=f"{self.http_api.url}webhook",
            description="GitHub webhook URL - configure this in your repository settings"
        )
        CfnOutput(
            self, "WebhookSecretArn",
            value=self.webhook_secret.secret_arn,
            description="ARN of the webhook secret - retrieve value to configure GitHub webhook"
        )
