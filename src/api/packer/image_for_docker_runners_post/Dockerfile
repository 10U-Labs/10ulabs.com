FROM debian:stable-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    jq \
    unzip \
    tar \
    ca-certificates \
    gnupg \
    sudo \
    procps \
    libicu72 \
    libssl3 \
    liblttng-ust1 \
    zlib1g \
    && rm -rf /var/lib/apt/lists/*

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf awscliv2.zip aws

# Set up runner user
RUN useradd -m -s /bin/bash runner && \
    echo "runner ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

# Install GitHub Actions runner
ARG RUNNER_VERSION=2.311.0
ARG RUNNER_ARCH=arm64
WORKDIR /home/runner

RUN curl -o actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz -L \
    https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz && \
    tar xzf actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz && \
    rm actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz && \
    chown -R runner:runner /home/runner

# Install Node.js (required by many actions)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

RUN npm install -g jsonlint

# Install Python (for Actions that need it)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages \
    pytest \
    boto3 \
    boto3-stubs \
    botocore \
    pylint \
    mypy \
    yamllint \
    PyYAML \
    dnspython \
    requests

ARG TERRAFORM_VERSION=1.14.0
RUN wget https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_arm64.zip && \
    unzip terraform_${TERRAFORM_VERSION}_linux_arm64.zip && \
    mv terraform /usr/local/bin/ && \
    rm terraform_${TERRAFORM_VERSION}_linux_arm64.zip

ARG PACKER_VERSION=latest
RUN PACKER_LATEST=$(curl -s https://checkpoint-api.hashicorp.com/v1/check/packer | jq -r '.current_version') && \
    wget https://releases.hashicorp.com/packer/${PACKER_LATEST}/packer_${PACKER_LATEST}_linux_arm64.zip && \
    unzip packer_${PACKER_LATEST}_linux_arm64.zip && \
    mv packer /usr/local/bin/ && \
    rm packer_${PACKER_LATEST}_linux_arm64.zip

RUN TFLINT_LATEST=$(curl -s https://api.github.com/repos/terraform-linters/tflint/releases/latest | jq -r '.tag_name' | sed 's/v//') && \
    wget https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_LATEST}/tflint_linux_arm64.zip && \
    unzip tflint_linux_arm64.zip && \
    mv tflint /usr/local/bin/ && \
    rm tflint_linux_arm64.zip

# Copy entrypoint script
COPY entrypoint.py /home/runner/entrypoint.py
RUN chmod +x /home/runner/entrypoint.py && \
    chown runner:runner /home/runner/entrypoint.py

USER runner
WORKDIR /home/runner

ENTRYPOINT ["/home/runner/entrypoint.py"]
CMD ["--repo", "", "--name", "", "--labels", "", "--token", ""]
