import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "api"))
sys.path.insert(0, str(Path(__file__).parent.parent / "test" / "api"))

import importlib.util
import aws_cdk as cdk
from aws_cdk.assertions import Template

config_path = Path(__file__).parent.parent / "src" / "api" / "config.json"
with open(config_path, encoding='utf-8') as f:
    config = json.load(f)

stack_path = Path(__file__).parent.parent / "src" / "api" / "stack.py"
spec = importlib.util.spec_from_file_location("api_stack", stack_path)
api_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api_module)

cdk_app = cdk.App()
api_stack = api_module.ApiStack(
    cdk_app,
    "TestApiStack",
    config=config,
    env=cdk.Environment(
        account=str(config["aws"]["account_id"]),
        region=config["aws"]["region"]
    )
)

cdk_template = Template.from_stack(api_stack)
template_json = cdk_template.to_json()
resources = template_json.get('Resources', {})

for logical_id in sorted(resources.keys()):
    resource = resources[logical_id]
    print(f"{logical_id}:{resource['Type']}")
