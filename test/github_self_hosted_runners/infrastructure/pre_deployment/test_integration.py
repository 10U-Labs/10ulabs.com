"""
Integration tests for the GitHub self-hosted runners CDK stacks.

Unlike the unit tests, these assertions load the real repository
configuration and synthesize both the VPC and webhook stacks together
to validate cross-stack behaviour without executing the global app entry
point or unrelated website infrastructure.
"""
import json
import sys
from pathlib import Path

import aws_cdk as cdk
from aws_cdk import assertions
import pytest

SRC_PATH = Path(__file__).parent.parent.parent.parent.parent / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from github_self_hosted_runners.infrastructure.vpc_stack import VpcStack
from github_self_hosted_runners.infrastructure.webhook_stack import WebhookStack


@pytest.fixture(scope="module")
def project_root() -> Path:
    """Repository root (git workspace)."""
    return Path(__file__).parent.parent.parent.parent.parent


@pytest.fixture(scope="module")
def runner_config(project_root: Path) -> dict:
    """Load the GitHub runners configuration used by the real stacks."""
    config_path = project_root / "config" / "github_self_hosted_runners.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Runner configuration not found: {config_path}")
    with config_path.open() as fp:
        return json.load(fp)


@pytest.fixture(scope="module")
def synthesized_stacks(runner_config: dict) -> dict:
    """
    Instantiate and synthesize the GitHub runners stacks using the real config.

    Returns helpful handles for the individual tests (templates, assembly, etc).
    """
    app = cdk.App()
    env = cdk.Environment(
        account=str(runner_config["aws"]["account_id"]),
        region=runner_config["aws"]["region"]
    )

    vpc_stack = VpcStack(app, "GitHubRunnersVpcTest", config=runner_config, env=env)
    webhook_stack = WebhookStack(
        app,
        "GitHubRunnersWebhookTest",
        vpc=vpc_stack.vpc,
        config=runner_config,
        env=env,
        description="Test stack for GitHub runners webhook infrastructure"
    )
    webhook_stack.add_dependency(vpc_stack)

    for key, value in {
        "ManagedBy": "CDK",
        "Project": "10UF",
        "Repository": "10U-Foundation/10ulabs.com",
    }.items():
        cdk.Tags.of(app).add(key, value)

    assembly: CloudAssembly = app.synth()

    return {
        "config": runner_config,
        "app": app,
        "assembly": assembly,
        "vpc_stack": vpc_stack,
        "webhook_stack": webhook_stack,
        "vpc_template": assertions.Template.from_stack(vpc_stack),
        "webhook_template": assertions.Template.from_stack(webhook_stack),
    }


def test_stacks_synthesize_successfully(synthesized_stacks):
    """Ensure synthesizing the GitHub runners stacks completes without errors."""
    assembly = synthesized_stacks["assembly"]
    # CloudAssembly stores the synthesized stacks; presence of artifacts implies success.
    stack_names = [artifact.stack_name for artifact in assembly.stacks]
    assert "GitHubRunnersVpcTest" in stack_names
    assert "GitHubRunnersWebhookTest" in stack_names


def test_vpc_has_no_costly_endpoints_or_nat(synthesized_stacks):
    """Validate the VPC template omits NAT gateways and VPC endpoints."""
    template: assertions.Template = synthesized_stacks["vpc_template"]
    template.resource_count_is("AWS::EC2::VPC", 1)
    template.resource_count_is("AWS::EC2::NatGateway", 0)
    template.resource_count_is("AWS::EC2::VPCEndpoint", 0)


def test_vpc_exports_public_subnets(synthesized_stacks):
    """Ensure the VPC stack publishes the subnet IDs for downstream stacks."""
    template: assertions.Template = synthesized_stacks["vpc_template"]
    template.has_output("PublicSubnetIds", {})
    template.has_output("VpcId", {})


def test_webhook_task_definition_matches_config(synthesized_stacks):
    """Task definition CPU/memory must align with configuration values."""
    config = synthesized_stacks["config"]
    template: assertions.Template = synthesized_stacks["webhook_template"]

    template.has_resource_properties(
        "AWS::ECS::TaskDefinition",
        {
            "Cpu": str(config["fargate_runners"]["cpu"]),
            "Memory": str(config["fargate_runners"]["memory"]),
            "RequiresCompatibilities": ["FARGATE"],
            "NetworkMode": "awsvpc",
        },
    )


def test_webhook_lambda_environment_includes_expected_vars(synthesized_stacks):
    """Lambda environment variables should reference repo and runner labels."""
    config = synthesized_stacks["config"]
    template: assertions.Template = synthesized_stacks["webhook_template"]

    template.has_resource_properties(
        "AWS::Lambda::Function",
        assertions.Match.object_like(
            {
                "Environment": assertions.Match.object_like(
                    {
                        "Variables": assertions.Match.object_like(
                            {
                                "RUNNER_LABELS": ",".join(config["fargate_runners"]["runner_labels"]),
                                "ECS_CLUSTER": assertions.Match.any_value(),
                                "TASK_DEFINITION": assertions.Match.any_value(),
                            }
                        )
                    }
                )
            }
        ),
    )


def test_webhook_lambda_has_run_task_permissions(synthesized_stacks):
    """The Lambda IAM policy must allow ecs:RunTask on the runner task definition."""
    template: assertions.Template = synthesized_stacks["webhook_template"]

    template.has_resource_properties(
        "AWS::IAM::Policy",
        assertions.Match.object_like(
            {
                "PolicyDocument": assertions.Match.object_like(
                    {
                        "Statement": assertions.Match.array_with(
                            [
                                assertions.Match.object_like(
                                    {
                                        "Action": "ecs:RunTask",
                                        "Effect": "Allow",
                                    }
                                )
                            ]
                        )
                    }
                )
            }
        ),
    )


def test_webhook_stack_exports_key_outputs(synthesized_stacks):
    """Cluster name, task definition ARN, and webhook URL should be exported."""
    template: assertions.Template = synthesized_stacks["webhook_template"]
    for output in ["WebhookUrl", "ClusterName", "TaskDefinitionArn"]:
        template.has_output(output, {})


def test_global_tags_present_on_stacks(synthesized_stacks):
    """Both stacks should receive the global CDK tags declared in app.py."""
    expected_tags = [
        {"Key": "ManagedBy", "Value": "CDK"},
        {"Key": "Project", "Value": "10UF"},
        {"Key": "Repository", "Value": "10U-Foundation/10ulabs.com"},
    ]

    vpc_template: assertions.Template = synthesized_stacks["vpc_template"]
    webhook_template: assertions.Template = synthesized_stacks["webhook_template"]

    vpc_template.has_resource_properties(
        "AWS::EC2::VPC",
        assertions.Match.object_like({"Tags": assertions.Match.array_with(expected_tags)}),
    )
    webhook_template.has_resource_properties(
        "AWS::ECS::Cluster",
        assertions.Match.object_like({"Tags": assertions.Match.array_with(expected_tags)}),
    )
