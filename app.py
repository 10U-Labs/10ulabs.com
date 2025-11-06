#!/usr/bin/env python3
import os
import sys
import json
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

github_self_hosted_runners_stack = GitHubSelfHostedRunnersStack(
    app,
    "GitHubSelfHostedRunners",
    config=runner_config,
    env=runner_env,
    description="Complete GitHub Actions self-hosted runners infrastructure (VPC, ECR, ECS, Lambda)"
)

import sys
import importlib.util
sys.path.insert(0, str(Path(__file__).parent / "src"))

spec = importlib.util.spec_from_file_location(
    "tenuf_infrastructure",
    Path(__file__).parent / "src" / "10uf.org" / "infrastructure" / "stack.py"
)
tenuf_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tenuf_module)
TenUFComStack = tenuf_module.TenUFComStack

website_config_paths = [
    Path(__file__).parent / "config" / "websites" / "10uf.org.json",
    Path(__file__).parent / "config" / "10uf.org.json"
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

    website_stack = TenUFComStack(
        app,
        "TenUFCom",
        config=website_config,
        env=website_env,
        description="Static website infrastructure for 10uf.org"
    )

cdk.Tags.of(app).add("ManagedBy", "CDK")
cdk.Tags.of(app).add("Project", "10UF")
cdk.Tags.of(app).add("Repository", "10U-Foundation/10uf.org")

app.synth()
