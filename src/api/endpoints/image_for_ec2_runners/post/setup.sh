#!/bin/bash
set -euo pipefail

__main__() {
    local arch=""
    local docker_key=""
    local runner_user=""
    local runner_version=""
    local version_codename=""
    local yq_version=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --runner-user)
                runner_user="$2"
                shift 2
                ;;
            --runner-version)
                runner_version="$2"
                shift 2
                ;;
            --yq-version)
                yq_version="$2"
                shift 2
                ;;
            *)
                echo "Error: Unknown argument: $1"
                usage
                ;;
        esac
    done

    if [[ -z "$runner_user" ]]; then
        echo "Error: --runner-user is required"
        usage
    elif [[ -z "$runner_version" ]]; then
        echo "Error: --runner-version is required"
        usage
    elif [[ -z "$yq_version" ]]; then
        echo "Error: --yq-version is required"
        usage
    else
        arch=$(dpkg --print-architecture)
        docker_key=/etc/apt/keyrings/docker.asc
        version_codename=$(grep '^VERSION_CODENAME=' /etc/os-release | cut -d= -f2)

        add_docker_apt_repository \
            --docker-key "$docker_key" \
            --version-codename "$version_codename"

        install_system_packages

        install_python_packages

        install_yq \
            --arch "$arch" \
            --yq-version "$yq_version"

        create_runner_user \
            --runner-user "$runner_user"

        install_github_actions_runner \
            --arch "$arch" \
            --runner-user "$runner_user" \
            --runner-version "$runner_version"

        install_ssm_agent \
            --arch "$arch"

        install_cloudwatch_agent \
            --arch "$arch"

        cleanup_temp_files
    fi
}

add_docker_apt_repository() {
    local docker_key=""
    local version_codename=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --docker-key)
                docker_key="$2"
                shift 2
                ;;
            --version-codename)
                version_codename="$2"
                shift 2
                ;;
        esac
    done

    if [[ -z "$docker_key" ]]; then
        echo "Error: ${FUNCNAME[0]} requires --docker-key"
        exit 1
    elif [[ -z "$version_codename" ]]; then
        echo "Error: ${FUNCNAME[0]} requires --version-codename"
        exit 1
    else
        install -m 0755 -d /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/debian/gpg -o "$docker_key"
        chmod a+r "$docker_key"
        echo -e "Types: deb\nURIs: https://download.docker.com/linux/debian\nSuites: $version_codename\nComponents: stable\nSigned-By: $docker_key" | \
            tee /etc/apt/sources.list.d/docker.sources > /dev/null
    fi
}

cleanup_temp_files() {
    rm -rf /tmp/*
}

create_runner_user() {
    local runner_user=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --runner-user)
                runner_user="$2"
                shift 2
                ;;
        esac
    done

    if [[ -z "$runner_user" ]]; then
        echo "Error: ${FUNCNAME[0]} requires --runner-user"
        exit 1
    else
        useradd -m -s /bin/bash "$runner_user"
        usermod -aG docker "$runner_user"
    fi
}

install_cloudwatch_agent() {
    local arch=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --arch)
                arch="$2"
                shift 2
                ;;
        esac
    done

    if [[ -z "$arch" ]]; then
        echo "Error: ${FUNCNAME[0]} requires --arch"
        exit 1
    else
        curl -sSL -o /tmp/amazon-cloudwatch-agent.deb \
            "https://s3.amazonaws.com/amazoncloudwatch-agent/debian/${arch}/latest/amazon-cloudwatch-agent.deb"
        dpkg -i /tmp/amazon-cloudwatch-agent.deb
    fi
}

install_github_actions_runner() {
    local arch=""
    local runner_user=""
    local runner_version=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --arch)
                arch="$2"
                shift 2
                ;;
            --runner-user)
                runner_user="$2"
                shift 2
                ;;
            --runner-version)
                runner_version="$2"
                shift 2
                ;;
        esac
    done

    if [[ -z "$arch" ]]; then
        echo "Error: ${FUNCNAME[0]} requires --arch"
        exit 1
    elif [[ -z "$runner_user" ]]; then
        echo "Error: ${FUNCNAME[0]} requires --runner-user"
        exit 1
    elif [[ -z "$runner_version" ]]; then
        echo "Error: ${FUNCNAME[0]} requires --runner-version"
        exit 1
    else
        sudo -u "$runner_user" curl -sSL -o /tmp/actions-runner.tar.gz \
            "https://github.com/actions/runner/releases/download/v${runner_version}/actions-runner-linux-${arch}-${runner_version}.tar.gz"
        sudo -u "$runner_user" mkdir -p "/home/$runner_user/actions-runner"
        sudo -u "$runner_user" tar xzf /tmp/actions-runner.tar.gz -C "/home/$runner_user/actions-runner"
        "/home/$runner_user/actions-runner/bin/installdependencies.sh"
    fi
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
    local arch=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --arch)
                arch="$2"
                shift 2
                ;;
        esac
    done

    if [[ -z "$arch" ]]; then
        echo "Error: ${FUNCNAME[0]} requires --arch"
        exit 1
    else
        curl -sSL -o /tmp/amazon-ssm-agent.deb \
            "https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/debian_${arch}/amazon-ssm-agent.deb"
        dpkg -i /tmp/amazon-ssm-agent.deb
        systemctl enable amazon-ssm-agent
    fi
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
    local arch=""
    local yq_version=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            --arch)
                arch="$2"
                shift 2
                ;;
            --yq-version)
                yq_version="$2"
                shift 2
                ;;
        esac
    done

    if [[ -z "$arch" ]]; then
        echo "Error: ${FUNCNAME[0]} requires --arch"
        exit 1
    elif [[ -z "$yq_version" ]]; then
        echo "Error: ${FUNCNAME[0]} requires --yq-version"
        exit 1
    else
        curl -sSL -o /usr/local/bin/yq "https://github.com/mikefarah/yq/releases/download/v${yq_version}/yq_linux_${arch}"
        chmod +x /usr/local/bin/yq
    fi
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

__main__ "$@"
