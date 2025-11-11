#!/usr/bin/env python3
import os
import sys
import json
import importlib.util
from pathlib import Path

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

import aws_cdk as cdk

from github_self_hosted_runners.infrastructure.github_self_hosted_runners_stack import GitHubSelfHostedRunnersStack
from github_self_hosted_runners.infrastructure.config import load_runner_config

app = cdk.App()

runner_config_path = Path(__file__).parent / "config" / "github_self_hosted_runners.json"
runner_config = load_runner_config(runner_config_path)

runner_env = cdk.Environment(
    account=str(runner_config["aws"]["account_id"]),
    region=runner_config["aws"]["region"]
)

# Domain Infrastructure (must be deployed first)
domain_spec = importlib.util.spec_from_file_location(
    "domain_infrastructure",
    Path(__file__).parent / "src" / "cloudtrail_and_domain_name" / "stack.py"
)
domain_module = importlib.util.module_from_spec(domain_spec)
domain_spec.loader.exec_module(domain_module)
DomainStack = domain_module.DomainStack

domain_config_path = Path(__file__).parent / "config" / "cloudtrail_and_domain_name.json"
if domain_config_path.exists():
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_env = cdk.Environment(
        account=str(domain_config["aws_account_id"]),
        region=domain_config["aws_region"]
    )

    domain_stack = DomainStack(
        app,
        "TenULabsDomainName",
        config=domain_config,
        env=domain_env,
        description="Route53 hosted zone for 10ulabs.com domain"
    )

github_self_hosted_runners_stack = GitHubSelfHostedRunnersStack(
    app,
    "GitHubSelfHostedRunners",
    config=runner_config,
    env=runner_env,
    description="Complete GitHub Actions self-hosted runners infrastructure (VPC, ECR, ECS, Lambda)"
)

# Website Infrastructure
spec = importlib.util.spec_from_file_location(
    "tenuf_infrastructure",
    Path(__file__).parent / "src" / "website" / "infrastructure" / "stack.py"
)
tenuf_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tenuf_module)
TenULabsComStack = tenuf_module.TenULabsComStack

website_config_paths = [
    Path(__file__).parent / "config" / "websites" / "website.json",
    Path(__file__).parent / "config" / "website.json"
]

website_config = None
for config_path in website_config_paths:
    if config_path.exists():
        with open(config_path) as f:
            website_config = json.load(f)
        break

if website_config and website_config.get("enabled", False):
    website_env = cdk.Environment(
        account=str(runner_config["aws"]["account_id"]),
        region=runner_config["aws"]["region"]
    )

    website_stack = TenULabsComStack(
        app,
        "TenULabsCom",
        config=website_config,
        env=website_env,
        description="Static website infrastructure for 10ulabs.com"
    )

# EC2 Spot Runner API
api_spec = importlib.util.spec_from_file_location(
    "ec2_spot_runner_api",
    Path(__file__).parent / "src" / "api" / "github_self_hosted_runners" / "ec2_spot_instance_based_runners" / "stack.py"
)
api_module = importlib.util.module_from_spec(api_spec)
api_spec.loader.exec_module(api_module)
EC2SpotRunnerAPIStack = api_module.EC2SpotRunnerAPIStack

api_config_path = Path(__file__).parent / "src" / "api" / "github_self_hosted_runners" / "ec2_spot_instance_based_runners" / "config.json"
if api_config_path.exists():
    with open(api_config_path) as f:
        api_config = json.load(f)

    api_env = cdk.Environment(
        account=str(api_config["aws_account_id"]),
        region=api_config["aws_region"]
    )

    ec2_spot_runner_api_stack = EC2SpotRunnerAPIStack(
        app,
        "EC2SpotRunnerAPI",
        config=api_config,
        env=api_env,
        description="API for launching EC2 spot instance GitHub self-hosted runners at api.10ulabs.com"
    )

cdk.Tags.of(app).add("ManagedBy", "CDK")
cdk.Tags.of(app).add("Project", "10UF")
cdk.Tags.of(app).add("Repository", "10U-Foundation/10ulabs.com")

app.synth()
