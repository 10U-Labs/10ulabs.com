#!/usr/bin/env python3
import json
import importlib.util
from pathlib import Path

import aws_cdk as cdk

spec = importlib.util.spec_from_file_location(
    "docker_runner_infrastructure",
    Path(__file__).parent / "stack.py"
)
if spec is None or spec.loader is None:
    raise RuntimeError("Failed to load docker_runner_infrastructure stack module")
docker_runner_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docker_runner_module)
DockerRunnerStack = docker_runner_module.DockerRunnerStack

app = cdk.App()

parent_config_path = Path(__file__).parent.parent.parent / "self" / "config.json"
with open(parent_config_path) as f:
    parent_config = json.load(f)

collection_config_path = Path(__file__).parent / "config.json"
with open(collection_config_path) as f:
    collection_config = json.load(f)

config = {**parent_config, **collection_config}

env = cdk.Environment(
    account=str(config["aws"]["account_id"]),
    region=config["aws"]["region"]
)

docker_runner_stack = DockerRunnerStack(
    app,
    "TenULabsApi-DockerRunner",
    config=config,
    env=env,
    description="Fargate Spot runner launcher for GitHub self-hosted runners"
)

cdk.Tags.of(app).add("ManagedBy", "CDK")
cdk.Tags.of(app).add("Project", "10UF")
cdk.Tags.of(app).add("Repository", "10U-Labs-LLC/10ulabs.com")

app.synth()
