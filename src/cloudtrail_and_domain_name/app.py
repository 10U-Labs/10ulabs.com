#!/usr/bin/env python3
import json
import importlib.util
from pathlib import Path

import aws_cdk as cdk

spec = importlib.util.spec_from_file_location(
    "domain_infrastructure",
    Path(__file__).parent / "stack.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("Failed to load domain_infrastructure stack module")
domain_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(domain_module)
DomainStack = domain_module.DomainStack

app = cdk.App()

config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
with open(config_path) as f:
    config = json.load(f)

env = cdk.Environment(
    account=str(config["aws_account_id"]),
    region=config["aws_region"]
)

domain_stack = DomainStack(
    app,
    "TenULabsDomainName",
    config=config,
    env=env,
    description="Route53 hosted zone for 10ulabs.com domain"
)

cdk.Tags.of(app).add("ManagedBy", "CDK")
cdk.Tags.of(app).add("Project", "10UF")
cdk.Tags.of(app).add("Repository", "10U-Foundation/10ulabs.com")

app.synth()
