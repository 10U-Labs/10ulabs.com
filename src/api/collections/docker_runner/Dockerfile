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
    && rm -rf /var/lib/apt/lists/*

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

# Install Python (for Actions that need it)
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Copy entrypoint script
COPY entrypoint.py /home/runner/entrypoint.py
RUN chmod +x /home/runner/entrypoint.py && \
    chown runner:runner /home/runner/entrypoint.py

USER runner
WORKDIR /home/runner

ENTRYPOINT ["/home/runner/entrypoint.py"]
