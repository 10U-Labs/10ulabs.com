#!/usr/bin/env python3
import argparse
import json
import logging
import os
import subprocess
import sys
import time
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format='%(message)s')

def create_secret_value(github_token: str, github_org: str, github_repo: str) -> dict:
    return {
        "auth_method": "classic-pat",
        "github_token": github_token,
        "github_org": github_org,
        "github_repo": github_repo,
        "created_by": "cdk-deploy",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

def update_secret(secret_name: str, github_token: str, github_org: str,
                 github_repo: str, region: str) -> int:
    logging.info("Updating GitHub PAT in AWS Secrets Manager")

    secrets_client = boto3.client('secretsmanager', region_name=region)
    secret_value = create_secret_value(github_token, github_org, github_repo)

    try:
        secrets_client.update_secret(
            SecretId=secret_name,
            SecretString=json.dumps(secret_value)
        )
        logging.info("Updated secret: %s", secret_name)
        return 0
    except ClientError as e:
        logging.error("Failed to update secret: %s", e)
        return 1

def run_cdk_deploy() -> int:
    logging.info("Running CDK deploy...")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    try:
        result = subprocess.run(
            ['cdk', 'deploy', '--require-approval', 'never'],
            check=True,
            capture_output=True,
            text=True
        )
        logging.info(result.stdout)
        if result.stderr:
            logging.warning(result.stderr)
        logging.info("CDK deploy completed successfully")
        return 0
    except subprocess.CalledProcessError as e:
        logging.error("CDK deploy failed")
        logging.error(e.stdout)
        logging.error(e.stderr)
        return 1

def main() -> int:
    parser = argparse.ArgumentParser(
        description='Deploy auth infrastructure using AWS CDK'
    )
    parser.add_argument('--github-token', help='GitHub personal access token')
    parser.add_argument('--skip-secret-update', action='store_true',
                       help='Skip updating the secret (deploy infrastructure only)')
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except IOError as e:
        logging.error("Failed to read config.json: %s", e)
        return 1

    result = run_cdk_deploy()
    if result != 0:
        return result

    if args.skip_secret_update:
        logging.info("Skipping secret update (--skip-secret-update specified)")
        return 0

    github_token = args.github_token or os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_RUNNER_PAT')
    if not github_token:
        logging.error("GitHub token not provided. Use --github-token or set GITHUB_TOKEN/GH_RUNNER_PAT env var")
        return 1

    return update_secret(
        config['aws']['secrets_manager']['github_pat_secret_name'],
        github_token,
        config['github']['org'],
        config['github']['repo'],
        config['aws']['region']
    )

if __name__ == '__main__':
    sys.exit(main())
