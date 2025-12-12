# Build stage - download and prepare all tools
FROM debian:stable-slim AS builder
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ARG NODE_VERSION
ARG RUNNER_ARCH
ARG RUNNER_VERSION
ARG TERRAFORM_VERSION
ARG YQ_VERSION
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl jq unzip xz-utils && \
    curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o /tmp/awscliv2.zip && \
    unzip -q /tmp/awscliv2.zip -d /tmp && \
    curl -fsSL -o /tmp/amazon-cloudwatch-agent.deb "https://amazoncloudwatch-agent.s3.amazonaws.com/debian/arm64/latest/amazon-cloudwatch-agent.deb" && \
    curl -fsSL -o /tmp/yq "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_arm64" && \
    chmod +x /tmp/yq && \
    HADOLINT_VERSION=$(curl -fsSL https://api.github.com/repos/hadolint/hadolint/releases/latest | jq -r '.tag_name') && \
    curl -fsSL -o /tmp/hadolint "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_VERSION}/hadolint-Linux-arm64" && \
    chmod +x /tmp/hadolint && \
    TFLINT_VERSION=$(curl -fsSL https://api.github.com/repos/terraform-linters/tflint/releases/latest | jq -r '.tag_name' | sed 's/v//') && \
    curl -fsSL -o /tmp/terraform.zip "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_arm64.zip" && \
    curl -fsSL -o /tmp/tflint.zip "https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_VERSION}/tflint_linux_arm64.zip" && \
    unzip -oq /tmp/terraform.zip -d /tmp && unzip -oq /tmp/tflint.zip -d /tmp && \
    mkdir -p /tmp/node && curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-arm64.tar.xz" | tar -xJ -C /tmp/node --strip-components=1 && \
    curl -fsSL -o /tmp/runner.tar.gz "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz" && \
    GH_VERSION=$(curl -fsSL https://api.github.com/repos/cli/cli/releases/latest | jq -r '.tag_name' | sed 's/v//') && \
    curl -fsSL -o /tmp/gh.tar.gz "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_arm64.tar.gz" && \
    mkdir -p /tmp/gh && tar -xzf /tmp/gh.tar.gz -C /tmp/gh --strip-components=1

# Runtime stage - minimal image with all tools
FROM debian:stable-slim
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
WORKDIR /home/runner
COPY --from=builder /tmp/aws /tmp/aws
COPY --from=builder /tmp/amazon-cloudwatch-agent.deb /tmp/
COPY --from=builder /tmp/yq /tmp/hadolint /tmp/terraform /tmp/tflint /tmp/gh/bin/gh /usr/local/bin/
COPY --from=builder /tmp/node /usr/local
COPY --from=builder /tmp/runner.tar.gz /tmp/
COPY entrypoint.py cloudwatch-agent-config.json /tmp/
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates curl fontconfig fonts-wqy-zenhei git jq wget \
        libatk-bridge2.0-0t64 libatk1.0-0t64 libatspi2.0-0t64 libavahi-client3 \
        libavahi-common3 libcairo2 libcups2t64 libdrm-amdgpu1 libdrm2 \
        libfontconfig1 libfreetype6 libgbm1 libgl1 libgl1-mesa-dri libglib2.0-0t64 \
        libglx-mesa0 libglx0 libharfbuzz0b libicu76 libasound2t64 liblttng-ust1 \
        libnss3 libpango-1.0-0 libsm6 libssl3t64 libthai0 libxaw7 libxcomposite1 \
        libxdamage1 libxext6 libxfixes3 libxfont2 libxi6 libxkbcommon0 libxmu6 \
        libxrandr2 libxt6t64 libxxf86vm1 mesa-libgallium procps python3 python3-pip \
        sudo tar unzip x11-xkb-utils xfonts-scalable xfonts-utils xserver-common xvfb zlib1g && \
    /tmp/aws/install && rm -rf /tmp/aws && \
    dpkg -i /tmp/amazon-cloudwatch-agent.deb && rm /tmp/amazon-cloudwatch-agent.deb && \
    npm install -g jsonlint && npm cache clean --force && \
    python3 -m pip install --no-cache-dir --break-system-packages \
        'boto3>=1.35.0' boto3-stubs 'botocore>=1.35.0' dockerfile-parse dnspython \
        mypy paramiko pylint pytest python-hcl2 PyYAML requests types-dockerfile-parse \
        types-paramiko types-PyYAML types-requests yamllint && \
    apt-get purge -y python3-pip && apt-get autoremove -y && \
    useradd -m -s /bin/bash runner && echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    tar xzf /tmp/runner.tar.gz && rm /tmp/runner.tar.gz && \
    mv /tmp/entrypoint.py /home/runner/entrypoint.py && chmod 755 /home/runner/entrypoint.py && \
    mv /tmp/cloudwatch-agent-config.json /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json && \
    chown -R runner:runner /home/runner && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* /var/log/* /tmp/*
USER runner
ENTRYPOINT ["/home/runner/entrypoint.py"]
CMD ["--repo", "", "--name", "", "--labels", "", "--token", ""]
