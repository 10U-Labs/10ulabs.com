#!/usr/bin/env python3
"""Entrypoint script for GitHub Actions self-hosted runner on Fargate."""
import argparse
import signal
import subprocess
import sys


def cleanup_runner(registration_token):
    """Remove the GitHub Actions runner registration."""
    print("Removing runner...")
    subprocess.run(
        ['./config.sh', 'remove', '--token', registration_token],
        check=False
    )


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

    def signal_handler(_signum, _frame):
        stop_cloudwatch_agent()
        cleanup_runner(registration_token)
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
        '--unattended'
    ], check=False)

    if config_result.returncode != 0:
        print(f"Error: config.sh failed with exit code {config_result.returncode}")
        sys.exit(1)

    start_cloudwatch_agent()

    print("Starting runner...")
    run_result = subprocess.run(['./run.sh'], check=False)

    stop_cloudwatch_agent()

    print(f"Runner exited with code {run_result.returncode}")
    sys.exit(run_result.returncode)


if __name__ == '__main__':
    main()
