#!/usr/bin/env python3
"""Entrypoint script for GitHub Actions self-hosted runner on Fargate.

Uses --ephemeral flag so runner auto-deregisters after one job.
"""
import argparse
import signal
import subprocess
import sys


def start_cloudwatch_agent():
    """Start the CloudWatch agent for log collection."""
    print("Starting CloudWatch agent...", flush=True)
    result = subprocess.run(
        ['sudo', '/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl',
         '-a', 'fetch-config', '-m', 'ec2', '-s',
         '-c', 'file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json'],
        check=False,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Warning: CloudWatch agent failed to start: {result.stderr}", flush=True)
    else:
        print("CloudWatch agent started successfully", flush=True)


def stop_cloudwatch_agent():
    """Stop the CloudWatch agent."""
    try:
        subprocess.run(
            ['sudo', '/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl',
             '-a', 'stop'],
            check=False,
            capture_output=True,
            timeout=3
        )
    except subprocess.TimeoutExpired:
        pass


def cleanup_runner(token: str) -> None:
    """Remove/deregister the runner from GitHub."""
    print("Deregistering runner...", flush=True)
    subprocess.run(
        ['./config.sh', '--remove', '--token', token],
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

    print("Registering GitHub Actions runner...", flush=True)
    print(f"Repository: {repo}", flush=True)
    print(f"Runner Name: {runner_name}", flush=True)
    print(f"Labels: {runner_labels}", flush=True)

    state = {"process": None}

    def signal_handler(_signum, _frame):
        print("Received shutdown signal, cleaning up...", flush=True)
        if state["process"] is not None:
            state["process"].terminate()
            try:
                state["process"].wait(timeout=3)
            except subprocess.TimeoutExpired:
                print("Runner did not exit, sending SIGKILL...", flush=True)
                state["process"].kill()
                try:
                    state["process"].wait(timeout=2)
                except subprocess.TimeoutExpired:
                    print("Runner still not dead after SIGKILL", flush=True)
        stop_cloudwatch_agent()
        print("Shutdown complete", flush=True)
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
        print(f"Error: config.sh failed with exit code {config_result.returncode}", flush=True)
        sys.exit(1)

    start_cloudwatch_agent()

    print("Starting runner...", flush=True)
    with subprocess.Popen(['./run.sh']) as process:
        state["process"] = process
        returncode = process.wait()

    stop_cloudwatch_agent()

    print(f"Runner exited with code {returncode}", flush=True)
    sys.exit(returncode)


if __name__ == '__main__':
    main()
