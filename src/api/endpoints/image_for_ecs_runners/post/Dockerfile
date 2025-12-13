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
    mkdir -p /staging/tmp /staging/usr/local/bin /staging/usr/local/lib && \
    curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o /tmp/awscliv2.zip && \
    unzip -q /tmp/awscliv2.zip -d /staging/tmp && \
    curl -fsSL -o /staging/tmp/amazon-cloudwatch-agent.deb "https://amazoncloudwatch-agent.s3.amazonaws.com/debian/arm64/latest/amazon-cloudwatch-agent.deb" && \
    curl -fsSL -o /staging/usr/local/bin/yq "https://github.com/mikefarah/yq/releases/download/v${YQ_VERSION}/yq_linux_arm64" && \
    chmod +x /staging/usr/local/bin/yq && \
    HADOLINT_VERSION=$(curl -fsSL https://api.github.com/repos/hadolint/hadolint/releases/latest | jq -r '.tag_name') && \
    curl -fsSL -o /staging/usr/local/bin/hadolint "https://github.com/hadolint/hadolint/releases/download/${HADOLINT_VERSION}/hadolint-Linux-arm64" && \
    chmod +x /staging/usr/local/bin/hadolint && \
    TFLINT_VERSION=$(curl -fsSL https://api.github.com/repos/terraform-linters/tflint/releases/latest | jq -r '.tag_name' | sed 's/v//') && \
    curl -fsSL -o /tmp/terraform.zip "https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_arm64.zip" && \
    curl -fsSL -o /tmp/tflint.zip "https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_VERSION}/tflint_linux_arm64.zip" && \
    unzip -oq /tmp/terraform.zip -d /staging/usr/local/bin && \
    unzip -oq /tmp/tflint.zip -d /staging/usr/local/bin && \
    curl -fsSL "https://nodejs.org/dist/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-arm64.tar.xz" | tar -xJ -C /tmp && \
    cp /tmp/node-v${NODE_VERSION}-linux-arm64/bin/node /staging/usr/local/bin/ && \
    cp -r /tmp/node-v${NODE_VERSION}-linux-arm64/lib/node_modules /staging/usr/local/lib/ && \
    ln -s ../lib/node_modules/npm/bin/npm-cli.js /staging/usr/local/bin/npm && \
    ln -s ../lib/node_modules/npm/bin/npx-cli.js /staging/usr/local/bin/npx && \
    curl -fsSL -o /staging/tmp/runner.tar.gz "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz" && \
    GH_VERSION=$(curl -fsSL https://api.github.com/repos/cli/cli/releases/latest | jq -r '.tag_name' | sed 's/v//') && \
    curl -fsSL "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_arm64.tar.gz" | \
        tar -xzf - -C /staging/usr/local/bin --strip-components=2 gh_${GH_VERSION}_linux_arm64/bin/gh

# Runtime stage - minimal image with all tools
FROM debian:stable-slim
SHELL ["/bin/bash", "-o", "pipefail", "-c"]
WORKDIR /home/runner
COPY --from=builder /staging /
COPY entrypoint.py cloudwatch-agent-config.json /tmp/
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates curl fontconfig git jq tar wget \
        libatk-bridge2.0-0t64 libatk1.0-0t64 libatspi2.0-0t64 libavahi-client3 \
        libavahi-common3 libcairo2 libcups2t64 libdrm-amdgpu1 libdrm2 \
        libfontconfig1 libfreetype6 libgbm1 libgl1 libgl1-mesa-dri libglib2.0-0t64 \
        libglx-mesa0 libglx0 libharfbuzz0b libicu76 libasound2t64 liblttng-ust1 \
        libnss3 libpango-1.0-0 libsm6 libssl3t64 libthai0 libxaw7 libxcomposite1 \
        libxdamage1 libxext6 libxfixes3 libxfont2 libxi6 libxkbcommon0 libxmu6 \
        libxrandr2 libxt6t64 libxxf86vm1 mesa-libgallium procps python3 python3-pip \
        sudo unzip x11-xkb-utils xfonts-scalable xfonts-utils xserver-common xvfb zlib1g && \
    /tmp/aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli && \
    rm -rf /tmp/aws && \
    dpkg -i /tmp/amazon-cloudwatch-agent.deb && rm /tmp/amazon-cloudwatch-agent.deb && \
    npm install -g jsonlint && npm cache clean --force && \
    python3 -m pip install --no-cache-dir --no-compile --break-system-packages \
        'boto3>=1.35.0' boto3-stubs 'botocore>=1.35.0' dockerfile-parse dnspython \
        mypy paramiko pylint PyJWT pytest python-hcl2 PyYAML requests types-dockerfile-parse \
        types-paramiko types-PyYAML types-requests yamllint && \
    apt-get autoremove -y && apt-get clean && \
    useradd -m -s /bin/bash runner && echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    tar xzf /tmp/runner.tar.gz && rm /tmp/runner.tar.gz && \
    mv /tmp/entrypoint.py /home/runner/entrypoint.py && chmod 755 /home/runner/entrypoint.py && \
    mv /tmp/cloudwatch-agent-config.json /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json && \
    chown -R runner:runner /home/runner && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* /var/cache/debconf/* \
           /var/log/* /tmp/* /root/.cache \
           /usr/share/doc/* /usr/share/man/* /usr/share/info/* /usr/share/locale/* \
           /usr/share/i18n/* && \
    find /usr -type f -name '*.pyc' -delete && \
    find /usr -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
USER runner
ENTRYPOINT ["/home/runner/entrypoint.py"]
CMD ["--repo", "", "--name", "", "--labels", "", "--token", ""]
