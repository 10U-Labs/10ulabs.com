FROM debian:stable-slim
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG NODE_VERSION
ARG RUNNER_ARCH
ARG RUNNER_VERSION
ARG TERRAFORM_VERSION
ARG YQ_VERSION

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        fontconfig \
        fonts-wqy-zenhei \
        git \
        gnupg \
        jq \
        libatk-bridge2.0-0t64 \
        libatk1.0-0t64 \
        libatspi2.0-0t64 \
        libavahi-client3 \
        libavahi-common3 \
        libcairo2 \
        libcups2t64 \
        libdrm-amdgpu1 \
        libdrm2 \
        libfontconfig1 \
        libfreetype6 \
        libgbm1 \
        libgl1 \
        libgl1-mesa-dri \
        libglib2.0-0t64 \
        libglx-mesa0 \
        libglx0 \
        libharfbuzz0b \
        libicu76 \
        liblttng-ust1 \
        libnss3 \
        libpango-1.0-0 \
        libsm6 \
        libssl3t64 \
        libthai0 \
        libxaw7 \
        libxext6 \
        libxfixes3 \
        libxfont2 \
        libxi6 \
        libxmu6 \
        libxrandr2 \
        libxt6t64 \
        libxxf86vm1 \
        mesa-libgallium \
        procps \
        python3 \
        python3-pip \
        python3-venv \
        sudo \
        tar \
        unzip \
        wget \
        x11-xkb-utils \
        xfonts-scalable \
        xfonts-utils \
        xserver-common \
        xvfb \
        xz-utils \
        zlib1g && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

RUN curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o awscliv2.zip && \
    unzip -q awscliv2.zip && \
    ./aws/install && \
    curl -fsSL -o /tmp/amazon-cloudwatch-agent.deb "https://amazoncloudwatch-agent.s3.amazonaws.com/debian/arm64/latest/amazon-cloudwatch-agent.deb" && \
    dpkg -i /tmp/amazon-cloudwatch-agent.deb && \
    rm /tmp/amazon-cloudwatch-agent.deb && \
    curl -fsSL -o /usr/local/bin/yq "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_arm64" && \
    chmod +x /usr/local/bin/yq && \
    HADOLINT_VERSION=$(curl -fsSL https://api.github.com/repos/hadolint/hadolint/releases/latest | jq -r '.tag_name') && \
    curl -fsSL -o /usr/local/bin/hadolint "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_VERSION}/hadolint-Linux-arm64" && \
    chmod +x /usr/local/bin/hadolint && \
    TFLINT_VERSION=$(curl -fsSL https://api.github.com/repos/terraform-linters/tflint/releases/latest | jq -r '.tag_name' | sed 's/v//') && \
    curl -fsSL -o terraform.zip "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_arm64.zip" && \
    curl -fsSL -o tflint.zip "https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_VERSION}/tflint_linux_arm64.zip" && \
    unzip -oq terraform.zip && \
    unzip -oq tflint.zip && \
    mv terraform tflint /usr/local/bin/ && \
    rm -rf awscliv2.zip aws terraform.zip tflint.zip && \
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
COPY --chmod=644 cloudwatch-agent-config.json /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

USER runner

ENTRYPOINT ["/home/runner/entrypoint.py"]
CMD ["--repo", "", "--name", "", "--labels", "", "--token", ""]
