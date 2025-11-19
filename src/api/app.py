#!/usr/bin/env python3
import json
import importlib.util
from pathlib import Path

import aws_cdk as cdk

spec = importlib.util.spec_from_file_location(
    "api_infrastructure",
    Path(__file__).parent / "stack.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("Failed to load api_infrastructure stack module")
api_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_module)
ApiStack = api_module.ApiStack

app = cdk.App()

config_path = Path(__file__).parent / "config.json"
with open(config_path, encoding='utf-8') as f:
    config = json.load(f)

env = cdk.Environment(
    account=str(config["aws"]["account_id"]),
    region=config["aws"]["region"]
)

api_stack = ApiStack(
    app,
    "TenULabsApi",
    config=config,
    env=env,
    description="API Gateway and Lambda infrastructure for api.10ulabs.com"
)

cdk.Tags.of(app).add("ManagedBy", "CDK")
cdk.Tags.of(app).add("Project", "10UF")
cdk.Tags.of(app).add("Repository", "10U-Foundation/10ulabs.com")

app.synth()
