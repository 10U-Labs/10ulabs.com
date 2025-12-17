#!/usr/bin/env python3
"""Entrypoint script for GitHub Actions self-hosted runner on Fargate.

Uses --ephemeral flag so runner auto-deregisters after one job.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import urllib.request


def start_cloudwatch_agent():
    """Start the CloudWatch agent for log collection."""
    print("Starting CloudWatch agent...")
    result = subprocess.run(
        ['sudo', '/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl',
         '-a', 'fetch-config', '-m', 'ec2', '-s',
         '-c', 'file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json'],
        check=False,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Warning: CloudWatch agent failed to start: {result.stderr}")
    else:
        print("CloudWatch agent started successfully")


def stop_cloudwatch_agent():
    """Stop the CloudWatch agent."""
    subprocess.run(
        ['sudo', '/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl',
         '-a', 'stop'],
        check=False,
        capture_output=True
    )


def get_removal_token(repo: str, pat: str) -> str:
    """Get a removal token from GitHub API."""
    url = f"https://api.github.com/repos/{repo}/actions/runners/remove-token"
    request = urllib.request.Request(url, method='POST')
    request.add_header('Authorization', f'token {pat}')
    request.add_header('Accept', 'application/vnd.github.v3+json')
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())
            return data.get('token', '')
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"Warning: Failed to get removal token: {e}")
        return ''


def cleanup_runner(repo: str) -> None:
    """Remove/deregister the runner from GitHub."""
    print("Deregistering runner...")
    pat = os.environ.get('GITHUB_PAT', '')
    if not pat:
        print("Warning: GITHUB_PAT not set, skipping deregistration")
        return
    removal_token = get_removal_token(repo, pat)
    if not removal_token:
        print("Warning: Could not get removal token, skipping deregistration")
        return
    subprocess.run(
        ['./config.sh', '--remove', '--token', removal_token],
        check=False,
        capture_output=True
    )


def main():
    """Main entry point for the runner script."""
    parser = argparse.ArgumentParser(description='GitHub Actions self-hosted runner for Fargate')
    parser.add_argument('--repo', required=True, help='GitHub repository (org/repo)')
    parser.add_argument('--name', required=True, help='Runner name')
    parser.add_argument('--labels', required=True, help='Comma-separated runner labels')
    parser.add_argument('--token', required=True, help='GitHub runner registration token')
    args = parser.parse_args()

    repo = args.repo
    runner_name = args.name
    runner_labels = args.labels
    registration_token = args.token

    print("Registering GitHub Actions runner...")
    print(f"Repository: {repo}")
    print(f"Runner Name: {runner_name}")
    print(f"Labels: {runner_labels}")

    state = {"process": None}

    def signal_handler(_signum, _frame):
        if state["process"] is not None:
            state["process"].terminate()
            try:
                state["process"].wait(timeout=5)
            except subprocess.TimeoutExpired:
                state["process"].kill()
                state["process"].wait()
        stop_cloudwatch_agent()
        cleanup_runner(repo)
        sys.exit(0)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    config_result = subprocess.run([
        './config.sh',
        '--url', f'https://github.com/{repo}',
        '--token', registration_token,
        '--name', runner_name,
        '--labels', runner_labels,
        '--work', '_work',
        '--unattended',
        '--ephemeral'
    ], check=False)

    if config_result.returncode != 0:
        print(f"Error: config.sh failed with exit code {config_result.returncode}")
        sys.exit(1)

    start_cloudwatch_agent()

    print("Starting runner...")
    with subprocess.Popen(['./run.sh']) as process:
        state["process"] = process
        returncode = process.wait()

    stop_cloudwatch_agent()

    print(f"Runner exited with code {returncode}")
    sys.exit(returncode)


if __name__ == '__main__':
    main()
