packer {
  required_plugins {
    amazon = {
      version = ">= 1.2.8"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

variable "os_family" {
  type        = string
  description = "OS family (debian, ubuntu, etc.)"
}

variable "os_version" {
  type        = string
  description = "OS version number"
}

variable "os_architecture" {
  type        = string
  description = "CPU architecture (arm64 or x86_64)"
}

variable "runner_version" {
  type        = string
  description = "GitHub Actions runner version"
}

variable "aws_region" {
  type        = string
  description = "AWS region"
}

variable "spot_instance_types" {
  type        = list(string)
  description = "List of instance types for spot diversification (capacity-optimized strategy)"
}

variable "subnet_id" {
  type        = string
  description = "Subnet ID for builder instance (should be in AZ supporting ARM/t4g instances)"
}

variable "github_repository" {
  type        = string
  description = "GitHub repository (org/repo format)"
  default     = ""
}

variable "github_workflow" {
  type        = string
  description = "GitHub workflow name"
  default     = ""
}

variable "github_run_id" {
  type        = string
  description = "GitHub workflow run ID"
  default     = ""
}

locals {
  timestamp = regex_replace(timestamp(), "[- TZ:]", "")
  ami_name  = "github-ec2-runner-${var.os_family}-${var.os_version}-${var.os_architecture}-${local.timestamp}"

  # Map architecture for AMI lookup
  ami_arch = var.os_architecture == "arm64" ? "arm64" : "amd64"

  # Map architecture for runner download
  runner_arch = var.os_architecture == "arm64" ? "arm64" : "x64"
}

# Data source to get the latest base OS AMI
data "amazon-ami" "base" {
  filters = {
    name                = "${var.os_family}-${var.os_version}-${local.ami_arch}-*"
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
  source_ami    = data.amazon-ami.base.id

  # Use spot instances for cost savings with capacity-optimized strategy
  # Diversify across instance types for better availability
  spot_price = "auto"
  spot_instance_types = var.spot_instance_types
  spot_allocation_strategy = "capacity-optimized"

  # Networking
  subnet_id = var.subnet_id

  # SSH configuration
  ssh_username = "admin"
  ssh_timeout  = "10m"

  # IAM instance profile for EC2 API access
  iam_instance_profile = "PackerEC2InstanceProfile"

  # AMI configuration
  ami_description = "GitHub Actions Runner - ${title(var.os_family)} ${var.os_version} ${var.os_architecture}"

  tags = merge(
    {
      Name            = "ami-${local.ami_name}"
      OSFamily        = title(var.os_family)
      OSVersion       = var.os_version
      OSArchitecture  = var.os_architecture
      RunnerVersion   = var.runner_version
      Purpose         = "GitHub self-hosted EC2 runner"
      Stable          = "false"
      BuildDate       = local.timestamp
    },
    var.github_repository != "" ? {
      ManagedBy  = "GitHubActions"
      Repository = var.github_repository
      Workflow   = var.github_workflow
      RunId      = var.github_run_id
    } : {}
  )

  # Snapshot tags
  snapshot_tags = {
    Name    = "snapshot-${local.ami_name}"
    Purpose = "GitHub self-hosted EC2 runner"
    Stable  = "false"
  }
}

build {
  name = "github-runner-ami"
  sources = ["source.amazon-ebs.github_runner"]

  # Wait for EC2 status checks to pass with exponential backoff
  provisioner "shell" {
    environment_vars = ["PYTHONUNBUFFERED=1"]
    script           = "${path.root}/wait_for_status_checks.py"
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
      "curl -fsSL https://download.docker.com/linux/${var.os_family}/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg",
      "sudo chmod a+r /etc/apt/keyrings/docker.gpg",
      "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${var.os_family} $(. /etc/os-release && echo $VERSION_CODENAME) stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null",
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
      "sudo -u github-runner bash -c 'cd /home/github-runner && mkdir -p actions-runner && cd actions-runner && curl -o actions-runner-linux-${local.runner_arch}-${var.runner_version}.tar.gz -L https://github.com/actions/runner/releases/download/v${var.runner_version}/actions-runner-linux-${local.runner_arch}-${var.runner_version}.tar.gz && tar xzf ./actions-runner-linux-${local.runner_arch}-${var.runner_version}.tar.gz'",
      "sudo chown -R github-runner:github-runner /home/github-runner/actions-runner"
    ]
  }

  # Install SSM agent
  provisioner "shell" {
    inline_shebang = "/bin/bash -e"
    inline = [
      "set -e",
      "cd /tmp",
      "wget -q https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/${var.os_family}_${var.os_architecture}/amazon-ssm-agent.deb",
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
      "wget -q https://s3.amazonaws.com/amazoncloudwatch-agent/${var.os_family}/${var.os_architecture}/latest/amazon-cloudwatch-agent.deb",
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
