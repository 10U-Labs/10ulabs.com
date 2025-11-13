#!/usr/bin/env python3
import json
import importlib.util
from pathlib import Path

import aws_cdk as cdk

spec = importlib.util.spec_from_file_location(
    "gmail_email_provider",
    Path(__file__).parent / "stack.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("Failed to load gmail_email_provider stack module")
gmail_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gmail_module)
GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

app = cdk.App()

config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
with open(config_path) as f:
    config = json.load(f)

env = cdk.Environment(
    account=str(config["aws"]["account_id"]),
    region=config["aws"]["region"]
)

gmail_stack = GmailEmailProviderStack(
    app,
    "GmailEmailProvider",
    config=config,
    env=env,
    description="Gmail email provider DNS configuration for 10ulabs.com"
)

cdk.Tags.of(app).add("ManagedBy", "CDK")
cdk.Tags.of(app).add("Project", "10UF")
cdk.Tags.of(app).add("Repository", "10U-Foundation/10ulabs.com")

app.synth()
