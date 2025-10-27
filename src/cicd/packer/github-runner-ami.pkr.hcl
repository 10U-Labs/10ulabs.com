packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.8"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

variable "debian_version" {
  type    = string
  default = "13"
  description = "Debian version number"
}

variable "architecture" {
  type    = string
  default = "arm64"
  description = "CPU architecture (arm64 or x86_64)"
}

variable "runner_version" {
  type    = string
  default = "2.311.0"
  description = "GitHub Actions runner version"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
  description = "AWS region"
}

variable "instance_type" {
  type    = string
  default = "c8gd.2xlarge"
  description = "EC2 instance type for building (spot instance)"
}

variable "vpc_id" {
  type    = string
  default = ""
  description = "VPC ID for builder instance"
}

variable "subnet_id" {
  type    = string
  default = ""
  description = "Subnet ID for builder instance"
}

locals {
  timestamp = regex_replace(timestamp(), "[- TZ:]", "")
  ami_name  = "github-runner-debian-${var.debian_version}-${var.architecture}-${local.timestamp}"

  # Map architecture for AMI lookup
  ami_arch = var.architecture == "arm64" ? "arm64" : "amd64"

  # Map architecture for runner download
  runner_arch = var.architecture == "arm64" ? "arm64" : "x64"
}

# Data source to get the latest Debian AMI
data "amazon-ami" "debian" {
  filters = {
    name                = "debian-${var.debian_version}-*-${local.ami_arch}-*"
    root-device-type    = "ebs"
    virtualization-type = "hvm"
  }
  most_recent = true
  owners      = ["136693071363"] # Debian official AWS account
  region      = var.aws_region
}

source "amazon-ebs" "github_runner" {
  ami_name      = local.ami_name
  instance_type = var.instance_type
  region        = var.aws_region
  source_ami    = data.amazon-ami.debian.id

  # Use spot instances for cost savings
  spot_price = "auto"
  spot_instance_types = [var.instance_type]

  # Networking
  vpc_id    = var.vpc_id
  subnet_id = var.subnet_id

  # SSH configuration
  ssh_username = "admin"
  ssh_timeout  = "10m"

  # AMI configuration
  ami_description = "GitHub Actions Runner - Debian ${var.debian_version} ${var.architecture}"

  tags = {
    Name          = local.ami_name
    OS            = "Debian"
    Version       = var.debian_version
    Architecture  = var.architecture
    RunnerVersion = var.runner_version
    Purpose       = "github-actions-runner"
    BuildDate     = local.timestamp
  }

  # Snapshot tags
  snapshot_tags = {
    Name    = "${local.ami_name}-snapshot"
    Purpose = "github-actions-runner"
  }
}

build {
  name = "github-runner-ami"
  sources = ["source.amazon-ebs.github_runner"]

  # Wait for EC2 status checks to pass with exponential backoff
  provisioner "shell" {
    inline = [
      "set -e",
      "echo 'Waiting for EC2 instance status checks to pass...'",
      "",
      "# Get instance ID using IMDSv2",
      "TOKEN=$(curl -X PUT 'http://169.254.169.254/latest/api/token' -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600')",
      "INSTANCE_ID=$(curl -H \"X-aws-ec2-metadata-token: $TOKEN\" http://169.254.169.254/latest/meta-data/instance-id)",
      "REGION=$(curl -H \"X-aws-ec2-metadata-token: $TOKEN\" http://169.254.169.254/latest/meta-data/placement/region)",
      "",
      "echo \"Instance ID: $INSTANCE_ID\"",
      "echo \"Region: $REGION\"",
      "",
      "# Install AWS CLI if not present",
      "if ! command -v aws &> /dev/null; then",
      "  echo 'Installing AWS CLI...'",
      "  curl 'https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip' -o 'awscliv2.zip'",
      "  unzip -q awscliv2.zip",
      "  sudo ./aws/install",
      "  rm -rf aws awscliv2.zip",
      "fi",
      "",
      "# Exponential backoff parameters (base 2)",
      "MAX_ATTEMPTS=10",
      "ATTEMPT=0",
      "BACKOFF=1",
      "",
      "while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do",
      "  ATTEMPT=$((ATTEMPT + 1))",
      "  echo \"Check attempt $ATTEMPT/$MAX_ATTEMPTS (waiting ${BACKOFF}s)...\"",
      "  ",
      "  # Check both instance status and system status",
      "  STATUS_OUTPUT=$(aws ec2 describe-instance-status \\",
      "    --instance-ids $INSTANCE_ID \\",
      "    --region $REGION \\",
      "    --query 'InstanceStatuses[0].[InstanceStatus.Status,SystemStatus.Status]' \\",
      "    --output text)",
      "  ",
      "  INSTANCE_STATUS=$(echo $STATUS_OUTPUT | awk '{print $1}')",
      "  SYSTEM_STATUS=$(echo $STATUS_OUTPUT | awk '{print $2}')",
      "  ",
      "  echo \"  Instance Status: $INSTANCE_STATUS\"",
      "  echo \"  System Status: $SYSTEM_STATUS\"",
      "  ",
      "  if [ \"$INSTANCE_STATUS\" = \"ok\" ] && [ \"$SYSTEM_STATUS\" = \"ok\" ]; then",
      "    echo \"✓ All status checks passed!\"",
      "    break",
      "  fi",
      "  ",
      "  if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then",
      "    echo \"✗ Status checks did not pass after $MAX_ATTEMPTS attempts\"",
      "    exit 1",
      "  fi",
      "  ",
      "  # Exponential backoff with base 2",
      "  sleep $BACKOFF",
      "  BACKOFF=$((BACKOFF * 2))",
      "done",
      "",
      "echo \"Instance is ready for provisioning\""
    ]
  }

  # Update system
  provisioner "shell" {
    inline = [
      "set -e",
      "export DEBIAN_FRONTEND=noninteractive",
      "sudo apt-get update",
      "sudo apt-get upgrade -y"
    ]
  }

  # Install base dependencies
  provisioner "shell" {
    inline = [
      "set -e",
      "export DEBIAN_FRONTEND=noninteractive",
      "sudo apt-get install -y \\",
      "  curl \\",
      "  wget \\",
      "  git \\",
      "  jq \\",
      "  unzip \\",
      "  sudo \\",
      "  ca-certificates \\",
      "  gnupg \\",
      "  lsb-release"
    ]
  }

  # Install Docker
  provisioner "shell" {
    inline = [
      "set -e",
      "sudo install -m 0755 -d /etc/apt/keyrings",
      "curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg",
      "sudo chmod a+r /etc/apt/keyrings/docker.gpg",
      "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null",
      "sudo apt-get update",
      "sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",
      "sudo systemctl enable docker"
    ]
  }

  # Create runner user
  provisioner "shell" {
    inline = [
      "set -e",
      "sudo useradd -m -s /bin/bash github-runner",
      "sudo usermod -aG docker github-runner"
    ]
  }

  # Install GitHub Actions runner
  provisioner "shell" {
    inline = [
      "set -e",
      "cd /home/github-runner",
      "sudo mkdir -p actions-runner",
      "cd actions-runner",
      "sudo curl -o actions-runner-linux-${local.runner_arch}-${var.runner_version}.tar.gz -L https://github.com/actions/runner/releases/download/v${var.runner_version}/actions-runner-linux-${local.runner_arch}-${var.runner_version}.tar.gz",
      "sudo tar xzf actions-runner-linux-${local.runner_arch}-${var.runner_version}.tar.gz",
      "sudo rm actions-runner-linux-${local.runner_arch}-${var.runner_version}.tar.gz",
      "sudo chown -R github-runner:github-runner /home/github-runner"
    ]
  }

  # Install CloudWatch agent
  provisioner "shell" {
    inline = [
      "set -e",
      "cd /tmp",
      "wget https://s3.amazonaws.com/amazoncloudwatch-agent/debian/${var.architecture}/latest/amazon-cloudwatch-agent.deb",
      "sudo dpkg -i -E ./amazon-cloudwatch-agent.deb",
      "rm amazon-cloudwatch-agent.deb"
    ]
  }

  # Cleanup
  provisioner "shell" {
    inline = [
      "set -e",
      "sudo apt-get clean",
      "sudo rm -rf /var/lib/apt/lists/*",
      "sudo rm -rf /tmp/*",
      "sudo rm -rf /var/tmp/*"
    ]
  }
}
