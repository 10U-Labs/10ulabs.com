#!/usr/bin/env python3
import json
import os
import signal
import socket
import subprocess
import sys
import urllib.request


def get_registration_token(github_token, repo):
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    req = urllib.request.Request(
        f'https://api.github.com/repos/{repo}/actions/runners/registration-token',
        method='POST',
        headers=headers
    )

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read())
            token = data.get('token')
            if not token or token == 'null':
                return None
            return token
    except Exception as e:
        print(f"Error getting registration token: {e}")
        return None


def cleanup_runner(registration_token):
    print("Removing runner...")
    subprocess.run(
        ['./config.sh', 'remove', '--token', registration_token],
        check=False
    )


def main():
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        print("Error: GITHUB_TOKEN is not set")
        sys.exit(1)

    repo = os.environ.get('GITHUB_REPO')
    if not repo:
        print("Error: GITHUB_REPO is not set")
        sys.exit(1)

    runner_labels = os.environ.get('RUNNER_LABELS', 'fargate,general')
    runner_group = os.environ.get('RUNNER_GROUP', 'default')
    runner_name = os.environ.get('RUNNER_NAME', f'fargate-runner-{socket.gethostname()}')

    print("Registering GitHub Actions runner...")
    print(f"Repository: {repo}")
    print(f"Runner Name: {runner_name}")
    print(f"Labels: {runner_labels}")

    registration_token = get_registration_token(github_token, repo)
    if not registration_token:
        print("Error: Failed to get registration token")
        sys.exit(1)

    def signal_handler(signum, frame):
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
