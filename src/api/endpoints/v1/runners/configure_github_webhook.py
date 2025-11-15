#!/usr/bin/env python3
"""
Configure GitHub repository webhook for self-hosted runners.

This script:
1. Gets webhook URL from CloudFormation stack
2. Gets webhook secret from Secrets Manager
3. Configures GitHub repository webhook to trigger runner launches

Run after infrastructure is deployed to enable webhook-triggered runners.
"""

import json
import subprocess
import sys


def main():
    stack_name = 'GitHubRunnersWebhook'
    secret_name = 'github-webhook-secret'
    region = 'us-east-1'
    repo = '10U-Foundation/10ulabs.com'

    print("===================================")
    print("GitHub Webhook Configuration")
    print("===================================")
    print()

    # Get webhook URL from CloudFormation
    print("Getting webhook URL from CloudFormation stack...")
    result = subprocess.run([
        'aws', 'cloudformation', 'describe-stacks',
        '--stack-name', stack_name,
        '--region', region,
        '--query', 'Stacks[0].Outputs[?OutputKey==`WebhookUrl`].OutputValue',
        '--output', 'text'
    ], capture_output=True, text=True, check=False)

    if result.returncode != 0 or not result.stdout.strip():
        print(f"ERROR: Could not get webhook URL from stack {stack_name}")
        sys.exit(1)

    webhook_url = result.stdout.strip()
    print(f"✓ Webhook URL: {webhook_url}")
    print()

    # Get webhook secret from Secrets Manager
    print("Getting webhook secret from Secrets Manager...")
    result = subprocess.run([
        'aws', 'secretsmanager', 'get-secret-value',
        '--secret-id', secret_name,
        '--region', region,
        '--query', 'SecretString',
        '--output', 'text'
    ], capture_output=True, text=True, check=False)

    if result.returncode != 0 or not result.stdout.strip():
        print("ERROR: Could not get webhook secret from Secrets Manager")
        sys.exit(1)

    webhook_secret = result.stdout.strip()
    print("✓ Webhook secret retrieved")
    print()

    # Configure GitHub webhook
    print("Configuring GitHub repository webhook...")
    result = subprocess.run([
        'gh', 'api', f'/repos/{repo}/hooks',
        '-X', 'POST',
        '-f', 'name=web',
        '-F', 'active=true',
        '-F', f'config[url]={webhook_url}',
        '-F', 'config[content_type]=application/json',
        '-F', f'config[secret]={webhook_secret}',
        '-F', 'config[insecure_ssl]=0',
        '-f', 'events[]=workflow_job',
        '--jq', '.id'
    ], capture_output=True, text=True, check=False)

    if result.returncode != 0:
        print(f"ERROR: Failed to configure webhook: {result.stderr}")
        sys.exit(1)

    webhook_id = result.stdout.strip()

    print("✓ Webhook configured!")
    print(f"  Webhook ID: {webhook_id}")
    print(f"  URL: {webhook_url}")
    print("  Event: workflow_job")
    print()
    print("===================================")
    print("Self-hosted runners enabled!")
    print("===================================")
    print()
    print("Jobs with labels will now trigger ephemeral runners:")
    print("  - 'ephemeral-ec2-spot-instance' → EC2 spot instances")
    print("  - 'ephemeral-ecs-fargate-spot' → Fargate spot tasks")
    print()
    print("Example workflow:")
    print("  runs-on: [self-hosted, docker-builder, ephemeral-ec2-spot-instance]")


if __name__ == '__main__':
    main()
