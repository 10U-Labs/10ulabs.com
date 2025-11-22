#!/usr/bin/env python3
import os
import signal
import subprocess
import sys


def cleanup_runner(registration_token):
    print("Removing runner...")
    subprocess.run(
        ['./config.sh', 'remove', '--token', registration_token],
        check=False
    )


def main():
    registration_token = os.environ.get('RUNNER_TOKEN')
    if not registration_token:
        print("Error: RUNNER_TOKEN is not set")
        sys.exit(1)

    repo = os.environ.get('GITHUB_REPO')
    if not repo:
        print("Error: GITHUB_REPO is not set")
        sys.exit(1)

    runner_labels = os.environ.get('RUNNER_LABELS', 'fargate,general')
    runner_name = os.environ.get('RUNNER_NAME', 'fargate-runner')

    print("Registering GitHub Actions runner...")
    print(f"Repository: {repo}")
    print(f"Runner Name: {runner_name}")
    print(f"Labels: {runner_labels}")

    def signal_handler(_signum, _frame):
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
        '--unattended',
        '--ephemeral'
    ], check=False)

    if config_result.returncode != 0:
        print(f"Error: config.sh failed with exit code {config_result.returncode}")
        sys.exit(1)

    print("Starting runner...")
    run_result = subprocess.run(['./run.sh'], check=False)

    print(f"Runner exited with code {run_result.returncode}")
    sys.exit(run_result.returncode)


if __name__ == '__main__':
    main()
