#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path


def run_command(cmd, check=True):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    if check and result.returncode != 0:
        print(f"ERROR: Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    return result


def main():
    print("Installing Docker...")

    subprocess.run(['sudo', 'install', '-m', '0755', '-d', '/etc/apt/keyrings'], check=True)

    print("Downloading Docker GPG key...")
    gpg_url = 'https://download.docker.com/linux/debian/gpg'
    gpg_path = '/etc/apt/keyrings/docker.gpg'

    result = subprocess.run([
        'curl', '-fsSL', gpg_url
    ], capture_output=True, check=True)

    subprocess.run([
        'sudo', 'gpg', '--dearmor', '-o', gpg_path
    ], input=result.stdout, check=True)

    subprocess.run(['sudo', 'chmod', 'a+r', gpg_path], check=True)

    arch_result = subprocess.run(['dpkg', '--print-architecture'], capture_output=True, text=True, check=True)
    arch = arch_result.stdout.strip()

    codename = None
    with open('/etc/os-release', 'r') as f:
        for line in f:
            if line.startswith('VERSION_CODENAME='):
                codename = line.split('=')[1].strip().strip('"')
                break

    if not codename:
        print("ERROR: Could not determine VERSION_CODENAME")
        sys.exit(1)

    print(f"Adding Docker repository for {arch} / {codename}...")
    repo_line = f'deb [arch={arch} signed-by={gpg_path}] https://download.docker.com/linux/debian {codename} stable\n'

    with open('/tmp/docker.list', 'w') as f:
        f.write(repo_line)

    subprocess.run([
        'sudo', 'tee', '/etc/apt/sources.list.d/docker.list'
    ], stdin=open('/tmp/docker.list'), stdout=subprocess.DEVNULL, check=True)

    print("Installing Docker packages...")
    run_command(['sudo', 'apt-get', 'update'])
    run_command([
        'sudo', 'apt-get', 'install', '-y',
        'docker-ce', 'docker-ce-cli', 'containerd.io',
        'docker-buildx-plugin', 'docker-compose-plugin'
    ])

    run_command(['sudo', 'systemctl', 'enable', 'docker'])

    print("Docker installed successfully")


if __name__ == '__main__':
    main()
