FROM debian:stable-slim
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN apt-get update && \
    apt-get install -y \
        ca-certificates \
        curl \
        git \
        gnupg \
        jq \
        libicu76 \
        libssl3t64 \
        liblttng-ust1 \
        procps \
        python3 \
        python3-pip \
        python3-venv \
        sudo \
        tar \
        unzip \
        wget \
        xz-utils \
        zlib1g && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip aws

RUN useradd -m -s /bin/bash runner && \
    echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

ARG RUNNER_VERSION=2.311.0
ARG RUNNER_ARCH=arm64
WORKDIR /home/runner

RUN curl -o actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz -L \
        https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz && \
    tar xzf actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz && \
    rm actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz && \
    chown -R runner:runner /home/runner

ARG NODE_VERSION=20.18.1
RUN curl -fsSL https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-arm64.tar.xz | \
        tar -xJ -C /usr/local --strip-components=1 && \
    npm install -g jsonlint && \
    npm cache clean --force

RUN pip3 install --no-cache-dir --break-system-packages \
        boto3 \
        boto3-stubs \
        botocore \
        dnspython \
        mypy \
        pylint \
        pytest \
        python-hcl2 \
        PyYAML \
        requests \
        types-PyYAML \
        types-requests \
        yamllint && \
    rm -rf /root/.cache/pip

ARG TERRAFORM_VERSION=1.14.0
RUN TFLINT_LATEST=$(curl -s https://api.github.com/repos/terraform-linters/tflint/releases/latest | jq -r '.tag_name' | sed 's/v//') && \
    curl -L -o "terraform_${TERRAFORM_VERSION}_linux_arm64.zip" "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_arm64.zip" && \
    curl -L -o "tflint_linux_arm64.zip" "https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_LATEST}/tflint_linux_arm64.zip" && \
    unzip "terraform_${TERRAFORM_VERSION}_linux_arm64.zip" && \
    unzip "tflint_linux_arm64.zip" && \
    mv terraform tflint /usr/local/bin/ && \
    rm -f ./*.zip

COPY entrypoint.py /home/runner/entrypoint.py
RUN chmod +x /home/runner/entrypoint.py && \
    chown runner:runner /home/runner/entrypoint.py

USER runner
WORKDIR /home/runner

ENTRYPOINT ["/home/runner/entrypoint.py"]
CMD ["--repo", "", "--name", "", "--labels", "", "--token", ""]
