#!/bin/bash
set -euo pipefail

RUNNER_VERSION=""
YQ_VERSION=""
RUNNER_USER=""
ARCH=""
VERSION_CODENAME=""
DOCKER_KEY=""

__main__() {
    parse_arguments "$@"
    validate_arguments
    set_environment_variables
    add_docker_apt_repository
    install_system_packages
    install_python_packages
    install_yq
    create_runner_user
    install_github_actions_runner
    install_ssm_agent
    install_cloudwatch_agent
    cleanup_temp_files
}

add_docker_apt_repository() {
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg -o "$DOCKER_KEY"
    chmod a+r "$DOCKER_KEY"
    echo -e "Types: deb\nURIs: https://download.docker.com/linux/debian\nSuites: $VERSION_CODENAME\nComponents: stable\nSigned-By: $DOCKER_KEY" | \
        tee /etc/apt/sources.list.d/docker.sources > /dev/null
}

cleanup_temp_files() {
    rm -rf /tmp/*
}

create_runner_user() {
    useradd -m -s /bin/bash "$RUNNER_USER"
    usermod -aG docker "$RUNNER_USER"
}

install_cloudwatch_agent() {
    curl -sSL -o /tmp/amazon-cloudwatch-agent.deb \
        "https://s3.amazonaws.com/amazoncloudwatch-agent/debian/${ARCH}/latest/amazon-cloudwatch-agent.deb"
    dpkg -i /tmp/amazon-cloudwatch-agent.deb
}

install_github_actions_runner() {
    sudo -u "$RUNNER_USER" curl -sSL -o /tmp/actions-runner.tar.gz \
        "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${ARCH}-${RUNNER_VERSION}.tar.gz"
    sudo -u "$RUNNER_USER" mkdir -p "/home/$RUNNER_USER/actions-runner"
    sudo -u "$RUNNER_USER" tar xzf /tmp/actions-runner.tar.gz -C "/home/$RUNNER_USER/actions-runner"
    "/home/$RUNNER_USER/actions-runner/bin/installdependencies.sh"
}

install_python_packages() {
    python3 -m pip install --break-system-packages \
        boto3 \
        boto3-stubs[ecr] \
        botocore \
        dnspython \
        dockerfile-parse \
        mypy \
        paramiko \
        pylint \
        pytest \
        python-hcl2 \
        pyyaml \
        requests \
        types-paramiko \
        types-PyYAML \
        types-dockerfile-parse \
        types-requests \
        yamllint
}

install_ssm_agent() {
    curl -sSL -o /tmp/amazon-ssm-agent.deb \
        "https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/debian_${ARCH}/amazon-ssm-agent.deb"
    dpkg -i /tmp/amazon-ssm-agent.deb
    systemctl enable amazon-ssm-agent
}

install_system_packages() {
    apt-get update
    apt-get install -y \
        containerd.io \
        docker-buildx-plugin \
        docker-ce \
        docker-ce-cli \
        docker-compose-plugin \
        git \
        jq \
        python3-pip \
        unzip \
        wget
    systemctl enable docker
}

install_yq() {
    curl -sSL -o /usr/local/bin/yq "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_${ARCH}"
    chmod +x /usr/local/bin/yq
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --runner-version)
                RUNNER_VERSION="$2"
                shift 2
                ;;
            --yq-version)
                YQ_VERSION="$2"
                shift 2
                ;;
            --runner-user)
                RUNNER_USER="$2"
                shift 2
                ;;
            *)
                echo "Error: Unknown argument: $1"
                usage
                ;;
        esac
    done
}

set_environment_variables() {
    ARCH=$(dpkg --print-architecture)
    VERSION_CODENAME=$(grep '^VERSION_CODENAME=' /etc/os-release | cut -d= -f2)
    DOCKER_KEY=/etc/apt/keyrings/docker.asc
}

usage() {
    echo "Usage: $0 --runner-version VERSION --yq-version VERSION --runner-user USER"
    echo ""
    echo "Required arguments:"
    echo "  --runner-version    GitHub Actions runner version (e.g., 2.330.0)"
    echo "  --yq-version        yq version (e.g., 4.44.1)"
    echo "  --runner-user       Username for the GitHub runner"
    exit 1
}

validate_arguments() {
    if [[ -z "$RUNNER_VERSION" ]]; then
        echo "Error: --runner-version is required"
        usage
    fi

    if [[ -z "$YQ_VERSION" ]]; then
        echo "Error: --yq-version is required"
        usage
    fi

    if [[ -z "$RUNNER_USER" ]]; then
        echo "Error: --runner-user is required"
        usage
    fi
}

__main__ "$@"
