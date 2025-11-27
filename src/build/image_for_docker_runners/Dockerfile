FROM debian:stable-slim
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG NODE_VERSION
ARG PACKER_VERSION
ARG RUNNER_ARCH
ARG RUNNER_VERSION
ARG TERRAFORM_VERSION
ARG YQ_VERSION

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        gnupg \
        jq \
        libicu76 \
        liblttng-ust1 \
        libssl3t64 \
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

RUN curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o awscliv2.zip && \
    unzip -q awscliv2.zip && \
    ./aws/install && \
    curl -fsSL -o /usr/local/bin/yq "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_arm64" && \
    chmod +x /usr/local/bin/yq && \
    HADOLINT_VERSION=$(curl -fsSL https://api.github.com/repos/hadolint/hadolint/releases/latest | jq -r '.tag_name') && \
    curl -fsSL -o /usr/local/bin/hadolint "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_VERSION}/hadolint-Linux-arm64" && \
    chmod +x /usr/local/bin/hadolint && \
    TFLINT_VERSION=$(curl -fsSL https://api.github.com/repos/terraform-linters/tflint/releases/latest | jq -r '.tag_name' | sed 's/v//') && \
    curl -fsSL -o terraform.zip "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_arm64.zip" && \
    curl -fsSL -o tflint.zip "https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_VERSION}/tflint_linux_arm64.zip" && \
    curl -fsSL -o packer.zip "https://releases.hashicorp.com/packer/${PACKER_VERSION}/packer_${PACKER_VERSION}_linux_arm64.zip" && \
    unzip -oq terraform.zip && \
    unzip -oq tflint.zip && \
    unzip -oq packer.zip && \
    mv terraform tflint packer /usr/local/bin/ && \
    rm -rf awscliv2.zip aws terraform.zip tflint.zip packer.zip && \
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-arm64.tar.xz" | \
        tar -xJ -C /usr/local --strip-components=1 && \
    npm install -g jsonlint && \
    npm cache clean --force && \
    python3 -m pip install --no-cache-dir --break-system-packages \
        boto3 \
        boto3-stubs \
        botocore \
        dockerfile-parse \
        dnspython \
        mypy \
        paramiko \
        pylint \
        pytest \
        python-hcl2 \
        PyYAML \
        requests \
        types-dockerfile-parse \
        types-paramiko \
        types-PyYAML \
        types-requests \
        yamllint

RUN useradd -m -s /bin/bash runner && \
    echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

WORKDIR /home/runner
RUN curl -fsSL -o runner.tar.gz \
        "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz" && \
    tar xzf runner.tar.gz && \
    rm runner.tar.gz && \
    chown -R runner:runner /home/runner

COPY --chown=runner:runner --chmod=755 entrypoint.py /home/runner/entrypoint.py

USER runner

ENTRYPOINT ["/home/runner/entrypoint.py"]
CMD ["--repo", "", "--name", "", "--labels", "", "--token", ""]
