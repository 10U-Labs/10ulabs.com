#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Install GitHub Actions runner')
    parser.add_argument('--runner-version', required=True, help='Runner version (e.g., 2.310.2)')
    parser.add_argument('--runner-arch', required=True, help='Architecture (arm64 or x64)')
    args = parser.parse_args()

    print(f"Installing GitHub Actions runner version {args.runner_version} for {args.runner_arch}...")

    runner_home = Path('/home/github-runner/actions-runner')
    subprocess.run(['sudo', 'mkdir', '-p', str(runner_home)], check=True)

    tarball_name = f'actions-runner-linux-{args.runner_arch}-{args.runner_version}.tar.gz'
    tarball_path = Path('/tmp') / tarball_name
    download_url = f'https://github.com/actions/runner/releases/download/v{args.runner_version}/{tarball_name}'

    print(f"Downloading from {download_url}...")
    try:
        urllib.request.urlretrieve(download_url, tarball_path)
    except Exception as e:
        print(f"ERROR: Failed to download runner: {e}")
        sys.exit(1)

    print(f"Extracting to {runner_home}...")
    subprocess.run([
        'sudo', 'tar', 'xzf', str(tarball_path),
        '-C', str(runner_home)
    ], check=True)

    tarball_path.unlink()

    print("Setting ownership...")
    subprocess.run([
        'sudo', 'chown', '-R', 'github-runner:github-runner',
        '/home/github-runner'
    ], check=True)

    print("GitHub Actions runner installed successfully")


if __name__ == '__main__':
    main()
