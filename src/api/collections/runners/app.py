#!/usr/bin/env python3
import json
import importlib.util
from pathlib import Path

import aws_cdk as cdk

spec = importlib.util.spec_from_file_location(
    "runners_infrastructure",
    Path(__file__).parent / "stack.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("Failed to load runners_infrastructure stack module")
runners_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runners_module)
RunnersStack = runners_module.RunnersStack

app = cdk.App()

config_path = Path(__file__).parent / "config.json"
with open(config_path) as f:
    config = json.load(f)

env = cdk.Environment(
    account=str(config["aws"]["account_id"]),
    region=config["aws"]["region"]
)

runners_stack = RunnersStack(
    app,
    "TenULabsApi-Runners",
    config=config,
    env=env,
    description="GitHub webhook router for self-hosted runners"
)

cdk.Tags.of(app).add("ManagedBy", "CDK")
cdk.Tags.of(app).add("Project", "10UF")
cdk.Tags.of(app).add("Repository", "10U-Labs-LLC/10ulabs.com")

app.synth()
