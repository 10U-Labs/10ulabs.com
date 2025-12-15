# Build stage - install dependencies
FROM debian:stable-slim AS builder
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip python3-venv && \
    python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage - minimal image
FROM debian:stable-slim
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/* /var/log/* /tmp/*
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1
WORKDIR /app
COPY main.py tools.py ./
COPY prompts/ ./prompts/
CMD ["python3", "main.py"]
