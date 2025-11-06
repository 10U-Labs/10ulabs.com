"""Unit tests for CDK infrastructure.

Unit tests for VPC and Webhook stacks.

These tests validate that individual CDK stacks are configured correctly
using template assertions to check resource properties and counts.
"""
import sys
from pathlib import Path

# Add src directory to path for imports (same as app.py)
src_path = Path(__file__).parent.parent.parent.parent.parent / "src"
sys.path.insert(0, str(src_path))

import aws_cdk as cdk
from aws_cdk import assertions
from github_self_hosted_runners.infrastructure.vpc_stack import VpcStack
from github_self_hosted_runners.infrastructure.webhook_stack import WebhookStack


def get_test_config():
    """Get test configuration"""
    return {
        "aws": {
            "account_id": "123456789012",
            "region": "us-east-1"
        },
        "vpc": {
            "cidr": "10.0.0.0/16",
            "max_azs": 99,  # Use all available AZs (us-east-1 has 6, CDK synth has 2)
            "nat_gateways": 0,
            "subnet_configuration": {
                "public_subnet_cidr_mask": 24
            }
        },
        "naming": {
            "vpc_name": "test-vpc",
            "cluster_name": "test-cluster",
            "task_family": "test-runner",
            "container_name": "test-runner",
            "log_stream_prefix": "test-runner",
            "lambda_function_name": "test-webhook-handler",
            "api_gateway_name": "test-webhook",
            "github_token_secret_name": "test-github-token",
            "webhook_secret_name": "test-webhook-secret"
        },
        "lambda": {
            "timeout_seconds": 30,
            "memory_mb": 256
        },
        "github": {
            "repo": "10U-Foundation/10uf.org"
        },
        "fargate_runners": {
            "cpu": "256",
            "memory": "512",
            "runner_labels": ["fargate", "general"],
            "log_retention_days": 7,
            "ecr_repository": "github-runner"
        }
    }


# ============================================================================
# VPC Stack Tests
# ============================================================================

def test_vpc_created():
    config = get_test_config()
    """Test that VPC is created with correct configuration"""
    app = cdk.App()

    stack = VpcStack(app, "test-vpc", config=config)
    template = assertions.Template.from_stack(stack)

    # Should have 2 subnets in test environment (CDK synth has 2 AZs available)
    # When deployed to us-east-1, will have 6 subnets (all 6 AZs)
    # Real validation of "uses all available AZs" happens in smoke tests
    template.resource_count_is("AWS::EC2::Subnet", 2)

    # Verify subnets are public (map public IP)
    template.has_resource_properties("AWS::EC2::Subnet", {
        "MapPublicIpOnLaunch": True
    })


def test_internet_gateway():
    config = get_test_config()
    """Test that Internet Gateway is attached"""
    app = cdk.App()

    stack = VpcStack(app, "test-vpc", config=config)
    template = assertions.Template.from_stack(stack)

    # Should have Internet Gateway
    template.resource_count_is("AWS::EC2::InternetGateway", 1)

    # Should have IGW attachment
    template.resource_count_is("AWS::EC2::VPCGatewayAttachment", 1)


def test_no_nat_gateways():
    config = get_test_config()
    """Test that NO NAT gateways are created (cost optimization)"""
    app = cdk.App()

    stack = VpcStack(app, "test-vpc", config=config)
    template = assertions.Template.from_stack(stack)

    # Should have ZERO NAT gateways
    template.resource_count_is("AWS::EC2::NatGateway", 0)


def test_no_vpc_endpoints():
    config = get_test_config()
    """Test that NO VPC endpoints are created (cost optimization)"""
    app = cdk.App()

    stack = VpcStack(app, "test-vpc", config=config)
    template = assertions.Template.from_stack(stack)

    # Should have NO VPC endpoints - runners use public internet
    # Cost savings: $86/month
    template.resource_count_is("AWS::EC2::VPCEndpoint", 0)


def test_vpc_stack_outputs():
    config = get_test_config()
    """Test that required VPC stack outputs are exported"""
    app = cdk.App()

    stack = VpcStack(app, "test-vpc", config=config)
    template = assertions.Template.from_stack(stack)

    # Should have VpcId output
    template.has_output("VpcId", {})

    # Should have VpcCidr output
    template.has_output("VpcCidr", {})

    # Should have PublicSubnetIds output
    template.has_output("PublicSubnetIds", {})

    # No EndpointSecurityGroupId output (removed with VPC endpoints for cost savings)


def test_vpc_tags():
    config = get_test_config()
    """Test that VPC is tagged correctly"""
    app = cdk.App()

    stack = VpcStack(app, "test-vpc", config=config)
    template = assertions.Template.from_stack(stack)

    # Verify VPC has purpose tag
    template.has_resource_properties("AWS::EC2::VPC", {
        "Tags": assertions.Match.array_with([
            {
                "Key": "Purpose",
                "Value": "github-runners"
            }
        ])
    })


# ============================================================================
# Webhook Stack Tests
# ============================================================================

def test_ecs_cluster_created():
    """Test that ECS cluster is created with container insights"""
    app = cdk.App()
    config = get_test_config()

    vpc_stack = VpcStack(app, "test-vpc", config=config)
    webhook_stack = WebhookStack(
        app, "test-webhook",
        vpc=vpc_stack.vpc,
        config=config
    )

    template = assertions.Template.from_stack(webhook_stack)

    # Should have ECS cluster
    template.resource_count_is("AWS::ECS::Cluster", 1)

    # Should have container insights enabled
    template.has_resource_properties("AWS::ECS::Cluster", {
        "ClusterSettings": [
            {
                "Name": "containerInsights",
                "Value": "enabled"
            }
        ]
    })


def test_task_definition_created():
    """Test that Fargate task definition is created with correct resources"""
    app = cdk.App()
    config = get_test_config()

    vpc_stack = VpcStack(app, "test-vpc", config=config)
    webhook_stack = WebhookStack(
        app, "test-webhook",
        vpc=vpc_stack.vpc,
        config=config
    )

    template = assertions.Template.from_stack(webhook_stack)

    # Should have task definition
    template.resource_count_is("AWS::ECS::TaskDefinition", 1)

    # Verify CPU and memory
    template.has_resource_properties("AWS::ECS::TaskDefinition", {
        "Cpu": "256",
        "Memory": "512",
        "RequiresCompatibilities": ["FARGATE"],
        "NetworkMode": "awsvpc"
    })


def test_task_definition_has_container():
    """Test that task definition has runner container with correct config"""
    app = cdk.App()
    config = get_test_config()

    vpc_stack = VpcStack(app, "test-vpc", config=config)
    webhook_stack = WebhookStack(
        app, "test-webhook",
        vpc=vpc_stack.vpc,
        config=config
    )

    template = assertions.Template.from_stack(webhook_stack)

    # Verify container definition uses config values
    template.has_resource_properties("AWS::ECS::TaskDefinition", {
        "ContainerDefinitions": assertions.Match.array_with([
            assertions.Match.object_like({
                "Name": config["naming"]["container_name"],
                "Environment": assertions.Match.array_with([
                    assertions.Match.object_like({
                        "Name": "GITHUB_REPO",
                        "Value": config["github"]["repo"]
                    }),
                    assertions.Match.object_like({
                        "Name": "EPHEMERAL",
                        "Value": "true"
                    })
                ])
            })
        ])
    })


def test_lambda_function_created():
    """Test that webhook Lambda function is created"""
    app = cdk.App()
    config = get_test_config()

    vpc_stack = VpcStack(app, "test-vpc", config=config)
    webhook_stack = WebhookStack(
        app, "test-webhook",
        vpc=vpc_stack.vpc,
        config=config
    )

    template = assertions.Template.from_stack(webhook_stack)

    # CDK creates 2 Lambda functions: webhook handler + LogRetention custom resource
    # So we check for at least 1, not exactly 1
    template.resource_count_is("AWS::Lambda::Function", 2)

    # Verify our webhook handler has correct config
    template.has_resource_properties("AWS::Lambda::Function", {
        "Runtime": "python3.11",
        "Handler": "webhook_runner_launcher.lambda_handler",
        "Timeout": 30,
        "MemorySize": 256
    })


def test_lambda_has_ecs_permissions():
    """Test that Lambda has permissions to run ECS tasks"""
    app = cdk.App()
    config = get_test_config()

    vpc_stack = VpcStack(app, "test-vpc", config=config)
    webhook_stack = WebhookStack(
        app, "test-webhook",
        vpc=vpc_stack.vpc,
        config=config
    )

    template = assertions.Template.from_stack(webhook_stack)

    # Should have IAM policy allowing ecs:RunTask
    # Use object_like to handle additional CDK-generated properties
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Action": "ecs:RunTask",
                    "Effect": "Allow"
                })
            ])
        }
    })


def test_lambda_has_passrole_permissions():
    """Test that Lambda can pass roles to ECS"""
    app = cdk.App()
    config = get_test_config()

    vpc_stack = VpcStack(app, "test-vpc", config=config)
    webhook_stack = WebhookStack(
        app, "test-webhook",
        vpc=vpc_stack.vpc,
        config=config
    )

    template = assertions.Template.from_stack(webhook_stack)

    # Should have IAM policy allowing iam:PassRole
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Action": "iam:PassRole",
                    "Effect": "Allow"
                })
            ])
        }
    })


def test_api_gateway_created():
    """Test that API Gateway HTTP API is created"""
    app = cdk.App()
    config = get_test_config()

    vpc_stack = VpcStack(app, "test-vpc", config=config)
    webhook_stack = WebhookStack(
        app, "test-webhook",
        vpc=vpc_stack.vpc,
        config=config
    )

    template = assertions.Template.from_stack(webhook_stack)

    # Should have HTTP API
    template.resource_count_is("AWS::ApiGatewayV2::Api", 1)

    # Verify protocol type
    template.has_resource_properties("AWS::ApiGatewayV2::Api", {
        "ProtocolType": "HTTP"
    })


def test_webhook_secret_created():
    """Test that webhook secret is created in Secrets Manager"""
    app = cdk.App()
    config = get_test_config()

    vpc_stack = VpcStack(app, "test-vpc", config=config)
    webhook_stack = WebhookStack(
        app, "test-webhook",
        vpc=vpc_stack.vpc,
        config=config
    )

    template = assertions.Template.from_stack(webhook_stack)

    # Should have webhook secret with config-driven name
    template.has_resource_properties("AWS::SecretsManager::Secret", {
        "Name": config["naming"]["webhook_secret_name"],
        "Description": "GitHub webhook secret for signature verification"
    })


def test_runner_security_group():
    """Test that security group is created for runner tasks"""
    app = cdk.App()
    config = get_test_config()

    vpc_stack = VpcStack(app, "test-vpc", config=config)
    webhook_stack = WebhookStack(
        app, "test-webhook",
        vpc=vpc_stack.vpc,
        config=config
    )

    template = assertions.Template.from_stack(webhook_stack)

    # Should have security group for runners
    template.has_resource_properties("AWS::EC2::SecurityGroup", {
        "GroupDescription": "Security group for GitHub runner Fargate tasks"
    })


def test_webhook_stack_outputs():
    """Test that required webhook stack outputs are exported"""
    app = cdk.App()
    config = get_test_config()

    vpc_stack = VpcStack(app, "test-vpc", config=config)
    webhook_stack = WebhookStack(
        app, "test-webhook",
        vpc=vpc_stack.vpc,
        config=config
    )

    template = assertions.Template.from_stack(webhook_stack)

    # Should have all required outputs
    template.has_output("WebhookUrl", {})
    template.has_output("WebhookSecretArn", {})
    template.has_output("ClusterName", {})
    template.has_output("TaskDefinitionArn", {})
    template.has_output("LambdaFunctionName", {})


def test_cloudwatch_logs():
    """Test that CloudWatch log groups are created"""
    app = cdk.App()
    config = get_test_config()

    vpc_stack = VpcStack(app, "test-vpc", config=config)
    webhook_stack = WebhookStack(
        app, "test-webhook",
        vpc=vpc_stack.vpc,
        config=config
    )

    template = assertions.Template.from_stack(webhook_stack)

    # Should have log groups for ECS task (CDK creates additional ones for custom resources)
    # Just check that at least 1 log group exists
    log_groups = template.find_resources("AWS::Logs::LogGroup")
    assert len(log_groups) >= 1, "Should have at least one CloudWatch log group"
