#!/usr/bin/env python3
import json
import os
import aws_cdk as cdk
from stack import AuthBetweenAwsAndGithubStack

app = cdk.App()

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

AuthBetweenAwsAndGithubStack(
    app,
    'AuthBetweenAwsAndGithub',
    config=config,
    env=cdk.Environment(
        account=config['aws']['account_id'],
        region=config['aws']['region']
    )
)

app.synth()
