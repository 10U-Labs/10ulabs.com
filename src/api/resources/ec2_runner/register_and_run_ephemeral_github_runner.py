#!/usr/bin/env python3
import json
import os
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path


def get_registration_token(github_token, repo):
    headers = {
        'Authorization': f'Bearer {github_token}',
        'Accept': 'application/vnd.github+json'
    }
    req = urllib.request.Request(
        f'https://api.github.com/repos/{repo}/actions/runners/registration-token',
        method='POST',
        headers=headers
    )

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            return data.get('token')
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        print(f"ERROR: Failed to get runner token: {e}")
        return None


def main():
    job_id = os.environ.get('JOB_ID')
    labels = os.environ.get('RUNNER_LABELS', '')
    github_token = os.environ.get('GITHUB_TOKEN')
    repo = os.environ.get('GITHUB_REPO')

    print("=== Ephemeral EC2 Spot Runner Setup ===")
    print(f"Job ID: {job_id}")
    print(f"Labels: {labels}")

    if not github_token or not repo:
        print("ERROR: GITHUB_TOKEN and GITHUB_REPO required")
        subprocess.run(['shutdown', '-h', 'now'], check=False)
        sys.exit(1)

    print("Getting registration token...")
    runner_token = get_registration_token(github_token, repo)

    if not runner_token:
        print("ERROR: Failed to get runner token")
        subprocess.run(['shutdown', '-h', 'now'], check=False)
        sys.exit(1)

    print("Got registration token, registering runner...")

    runner_dir = Path('/home/github-runner/actions-runner')
    hostname = socket.gethostname()
    runner_name = f'ec2-spot-{hostname}'

    print("Running config.sh...")
    config_result = subprocess.run([
        'sudo', '-u', 'github-runner',
        str(runner_dir / 'config.sh'),
        '--url', f'https://github.com/{repo}',
        '--token', runner_token,
        '--name', runner_name,
        '--labels', labels,
        '--ephemeral',
        '--unattended'
    ], cwd=runner_dir, check=False)

    print(f"config.sh completed with exit code: {config_result.returncode}")

    runner_file = runner_dir / '.runner'
    print(f"Checking for {runner_file}...")

    if not runner_file.exists():
        print("ERROR: Runner registration failed - .runner file not created")
        print(f"Directory contents of {runner_dir}:")
        subprocess.run(['ls', '-la', str(runner_dir)], check=False)
        subprocess.run(['shutdown', '-h', 'now'], check=False)
        sys.exit(1)

    print("Runner registered successfully, starting job execution...")

    run_result = subprocess.run([
        'sudo', '-u', 'github-runner',
        str(runner_dir / 'run.sh')
    ], cwd=runner_dir, check=False)

    print(f"Job completed with exit code: {run_result.returncode}, self-terminating...")

    try:
        metadata_result = subprocess.run(
            ['ec2-metadata', '--instance-id'],
            capture_output=True,
            text=True,
            check=True
        )
        instance_id = metadata_result.stdout.split()[-1]

        subprocess.run([
            'aws', 'ec2', 'terminate-instances',
            '--instance-ids', instance_id,
            '--region', os.environ.get('AWS_REGION', 'us-east-1')
        ], check=False)
    except (subprocess.SubprocessError, OSError) as e:
        print(f"Warning: Self-termination failed: {e}")
        subprocess.run(['shutdown', '-h', 'now'], check=False)


if __name__ == '__main__':
    main()
