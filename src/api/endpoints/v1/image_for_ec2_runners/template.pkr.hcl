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
  default = "t4g.large"
  description = "Primary EC2 instance type for building (spot instance)"
}

variable "spot_instance_types" {
  type    = list(string)
  default = ["t4g.large", "t4g.medium", "t4g.small"]
  description = "List of instance types for spot diversification (capacity-optimized strategy)"
}

variable "vpc_id" {
  type    = string
  default = ""
  description = "VPC ID for builder instance"
}

variable "subnet_id" {
  type    = string
  default = ""
  description = "Subnet ID for builder instance (should be in AZ supporting ARM/t4g instances)"
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
    name                = "debian-${var.debian_version}-${local.ami_arch}-*"
    root-device-type    = "ebs"
    virtualization-type = "hvm"
  }
  most_recent = true
  owners      = ["136693071363"] # Debian official AWS account
  region      = var.aws_region
}

source "amazon-ebs" "github_runner" {
  ami_name      = local.ami_name
  region        = var.aws_region
  source_ami    = data.amazon-ami.debian.id

  # Use spot instances for cost savings with capacity-optimized strategy
  # Diversify across instance types for better availability
  spot_price = "auto"
  spot_instance_types = var.spot_instance_types
  spot_allocation_strategy = "capacity-optimized"

  # Networking - use explicit subnet_id if provided, otherwise use subnet_filter
  vpc_id = var.vpc_id
  subnet_id = var.subnet_id != "" ? var.subnet_id : null

  # Only use subnet_filter if subnet_id not provided
  dynamic "subnet_filter" {
    for_each = var.subnet_id == "" ? [1] : []
    content {
      filters = {
        "vpc-id": var.vpc_id
        "map-public-ip-on-launch": "true"
      }
      random = true
    }
  }

  # SSH configuration
  ssh_username = "admin"
  ssh_timeout  = "10m"

  # IAM instance profile for EC2 API access
  iam_instance_profile = "PackerEC2InstanceProfile"

  # AMI configuration
  ami_description = "GitHub Actions Runner - Debian ${var.debian_version} ${var.architecture}"

  tags = {
    Name          = local.ami_name
    OS            = "Debian"
    Version       = var.debian_version
    Architecture  = var.architecture
    RunnerVersion = var.runner_version
    Purpose       = "Github self-hosted EC2 runner"
    stable        = "true"
    BuildDate     = local.timestamp
  }

  # Snapshot tags
  snapshot_tags = {
    Name    = "${local.ami_name}-snapshot"
    Purpose = "Github self-hosted EC2 runner"
    stable  = "true"
  }
}

build {
  name = "github-runner-ami"
  sources = ["source.amazon-ebs.github_runner"]

  # Wait for EC2 status checks to pass with exponential backoff
  provisioner "shell" {
    script = "${path.root}/wait_for_status_checks.py"
  }

  # Update system
  provisioner "shell" {
    inline_shebang = "/bin/bash -e"
    inline = [
      "set -e",
      "export DEBIAN_FRONTEND=noninteractive",
      "sudo apt-get update",
      "sudo apt-get upgrade -y"
    ]
  }

  # Install base dependencies
  provisioner "shell" {
    inline_shebang = "/bin/bash -e"
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
    inline_shebang = "/bin/bash -e"
    inline = [
      "set -e",
      "export DEBIAN_FRONTEND=noninteractive",
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
    inline_shebang = "/bin/bash -e"
    inline = [
      "set -e",
      "sudo useradd -m -s /bin/bash github-runner",
      "sudo usermod -aG docker github-runner"
    ]
  }

  # Install GitHub Actions runner
  provisioner "shell" {
    inline_shebang = "/bin/bash -e"
    inline = [
      "set -e",
      "cd /home/github-runner",
      "sudo -u github-runner mkdir -p actions-runner",
      "cd actions-runner",
      "sudo -u github-runner curl -o actions-runner-linux-${local.runner_arch}-${var.runner_version}.tar.gz -L https://github.com/actions/runner/releases/download/v${var.runner_version}/actions-runner-linux-${local.runner_arch}-${var.runner_version}.tar.gz",
      "sudo -u github-runner tar xzf ./actions-runner-linux-${local.runner_arch}-${var.runner_version}.tar.gz",
      "sudo chown -R github-runner:github-runner /home/github-runner/actions-runner"
    ]
  }

  # Install SSM agent
  provisioner "shell" {
    inline_shebang = "/bin/bash -e"
    inline = [
      "set -e",
      "cd /tmp",
      "wget -q https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/debian_${var.architecture}/amazon-ssm-agent.deb",
      "sudo dpkg -i -E ./amazon-ssm-agent.deb",
      "sudo systemctl enable amazon-ssm-agent",
      "rm amazon-ssm-agent.deb"
    ]
  }

  # Install CloudWatch agent
  provisioner "shell" {
    inline_shebang = "/bin/bash -e"
    inline = [
      "set -e",
      "cd /tmp",
      "wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/debian/${var.architecture}/latest/amazon-cloudwatch-agent.deb",
      "sudo dpkg -i -E ./amazon-cloudwatch-agent.deb",
      "rm amazon-cloudwatch-agent.deb"
    ]
  }

  # Cleanup
  provisioner "shell" {
    inline_shebang = "/bin/bash -e"
    inline = [
      "set -e",
      "sudo apt-get clean",
      "sudo rm -rf /var/lib/apt/lists/*",
      "sudo rm -rf /tmp/*",
      "sudo rm -rf /var/tmp/*"
    ]
  }
}
