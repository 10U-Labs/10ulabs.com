#!/usr/bin/env python3
"""EC2 runner AMI setup script."""
import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: str) -> None:
    """Run a shell command, stream output in real-time."""
    print(f"Running: {cmd}", flush=True)
    with subprocess.Popen(
        cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    ) as process:
        if process.stdout:
            for line in process.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)


def get_arch() -> str:
    """Get the system architecture."""
    return subprocess.check_output(
        ["dpkg", "--print-architecture"]
    ).decode().strip()


def get_version_codename() -> str:
    """Get the OS version codename from /etc/os-release."""
    os_release = Path("/etc/os-release").read_text(encoding="utf-8")
    for line in os_release.splitlines():
        if line.startswith("VERSION_CODENAME="):
            return line.split("=")[1].strip()
    raise RuntimeError("VERSION_CODENAME not found in /etc/os-release")


def add_docker_apt_repository(version_codename: str) -> None:
    """Add Docker APT repository."""
    docker_key = "/etc/apt/keyrings/docker.asc"
    run("install -m 0755 -d /etc/apt/keyrings")
    run(f"curl -fsSL https://download.docker.com/linux/debian/gpg -o {docker_key}")
    run(f"chmod a+r {docker_key}")
    sources_content = f"""Types: deb
URIs: https://download.docker.com/linux/debian
Suites: {version_codename}
Components: stable
Signed-By: {docker_key}
"""
    Path("/etc/apt/sources.list.d/docker.sources").write_text(sources_content)


def add_github_cli_apt_repository() -> None:
    """Add GitHub CLI APT repository."""
    keyring = "/etc/apt/keyrings/githubcli-archive-keyring.gpg"
    run("install -m 0755 -d /etc/apt/keyrings")
    run(f"curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg "
        f"-o {keyring}")
    run(f"chmod go+r {keyring}")
    arch = get_arch()
    sources_content = f"""Types: deb
URIs: https://cli.github.com/packages
Suites: stable
Components: main
Architectures: {arch}
Signed-By: {keyring}
"""
    Path("/etc/apt/sources.list.d/github-cli.sources").write_text(sources_content)


def install_system_packages() -> None:
    """Install system packages via apt."""
    run("apt-get update")
    packages = [
        "containerd.io",
        "docker-buildx-plugin",
        "docker-ce",
        "docker-ce-cli",
        "docker-compose-plugin",
        "gh",
        "git",
        "jq",
        "nodejs",
        "npm",
        "python3-pip",
        "unzip",
        "wget",
    ]
    run(f"apt-get install -y {' '.join(packages)}")
    run("systemctl enable docker")


def install_python_packages() -> None:
    """Install Python packages via pip."""
    packages = [
        "boto3",
        "boto3-stubs[ecr]",
        "botocore",
        "dnspython",
        "dockerfile-parse",
        "mypy",
        "paramiko",
        "pylint",
        "pytest",
        "python-hcl2",
        "pyyaml",
        "requests",
        "types-paramiko",
        "types-PyYAML",
        "types-dockerfile-parse",
        "types-requests",
        "yamllint",
    ]
    run(f"python3 -m pip install --break-system-packages {' '.join(packages)}")


def install_yq(arch: str, version: str) -> None:
    """Install yq YAML processor."""
    url = f"https://github.com/mikefarah/yq/releases/download/v{version}/yq_linux_{arch}"
    run(f"curl -sSL -o /usr/local/bin/yq {url}")
    run("chmod +x /usr/local/bin/yq")


def install_jsonlint() -> None:
    """Install jsonlint for JSON validation."""
    run("npm install -g jsonlint")


def create_runner_user(username: str) -> None:
    """Create the GitHub runner user."""
    run(f"useradd -m -s /bin/bash {username}")
    run(f"usermod -aG docker {username}")


def install_github_actions_runner(arch: str, username: str, version: str) -> None:
    """Install GitHub Actions runner."""
    url = (f"https://github.com/actions/runner/releases/download/"
           f"v{version}/actions-runner-linux-{arch}-{version}.tar.gz")
    run(f"sudo -u {username} curl -sSL -o /tmp/actions-runner.tar.gz {url}")
    run(f"sudo -u {username} mkdir -p /home/{username}/actions-runner")
    run(f"sudo -u {username} tar xzf /tmp/actions-runner.tar.gz "
        f"-C /home/{username}/actions-runner")
    run(f"/home/{username}/actions-runner/bin/installdependencies.sh")


def install_ssm_agent(arch: str) -> None:
    """Install AWS SSM agent."""
    url = (f"https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/"
           f"latest/debian_{arch}/amazon-ssm-agent.deb")
    run(f"curl -sSL -o /tmp/amazon-ssm-agent.deb {url}")
    run("dpkg -i /tmp/amazon-ssm-agent.deb")
    run("systemctl enable amazon-ssm-agent")


def install_cloudwatch_agent(arch: str) -> None:
    """Install AWS CloudWatch agent."""
    url = (f"https://s3.amazonaws.com/amazoncloudwatch-agent/"
           f"debian/{arch}/latest/amazon-cloudwatch-agent.deb")
    run(f"curl -sSL -o /tmp/amazon-cloudwatch-agent.deb {url}")
    run("dpkg -i /tmp/amazon-cloudwatch-agent.deb")


def cleanup_temp_files() -> None:
    """Remove temporary files."""
    run("rm -rf /tmp/*")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Setup EC2 runner AMI")
    parser.add_argument("--runner-user", required=True, help="GitHub runner username")
    parser.add_argument("--runner-version", required=True, help="GitHub runner version")
    parser.add_argument("--yq-version", required=True, help="yq version")
    args = parser.parse_args()

    arch = get_arch()
    version_codename = get_version_codename()

    add_docker_apt_repository(version_codename)
    add_github_cli_apt_repository()
    install_system_packages()
    install_python_packages()
    install_yq(arch, args.yq_version)
    install_jsonlint()
    create_runner_user(args.runner_user)
    install_github_actions_runner(arch, args.runner_user, args.runner_version)
    install_ssm_agent(arch)
    install_cloudwatch_agent(arch)
    cleanup_temp_files()

    print("Setup completed successfully", flush=True)


if __name__ == "__main__":
    main()
