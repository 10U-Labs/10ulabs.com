packer {
  required_version = ">= 1.8.0"
  required_plugins {
    amazon = {
      version = ">= 1.0.0"
      source  = "github.com/hashicorp/amazon"
    }
  }
}

variable "source_ami_id" {
  type        = string
  description = "Source AMI ID (our custom github-runner AMI with Docker)"
}

variable "instance_type" {
  type    = string
  default = "t4g.large"
}

variable "spot_instance_types" {
  type    = list(string)
  default = ["t4g.large", "t4g.medium", "t4g.small"]
}

variable "spot_max_price" {
  type    = string
  default = "0.05"
}

variable "subnet_id" {
  type        = string
  description = "Subnet ID for builder instance"
}

variable "runner_version" {
  type    = string
  default = "2.311.0"
}

variable "architecture" {
  type    = string
  default = "arm64"
}

variable "ecr_repository" {
  type    = string
  default = "github-runner-fargate"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "aws_account_id" {
  type        = string
  description = "AWS account ID"
}

locals {
  timestamp = regex_replace(timestamp(), "[- TZ:]", "")
}

source "amazon-ebs" "docker-builder" {
  ami_name      = "packer-docker-builder-temp-${local.timestamp}"
  region        = var.aws_region
  source_ami    = var.source_ami_id
  subnet_id     = var.subnet_id

  # Use spot instances with fallback types (don't set instance_type when using spot_instance_types)
  spot_price               = var.spot_max_price
  spot_instance_types      = var.spot_instance_types
  spot_allocation_strategy = "capacity-optimized"

  # IAM instance profile for ECR access
  iam_instance_profile = "PackerDockerBuilderRole"

  ssh_username = "admin"

  # Minimal storage (we don't care about the AMI)
  launch_block_device_mappings {
    device_name = "/dev/xvda"
    volume_size = 8
    volume_type = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name        = "packer-docker-builder-temp"
    Purpose     = "temporary-docker-build"
    DeleteAfter = local.timestamp
  }
}

build {
  sources = ["source.amazon-ebs.docker-builder"]

  # Upload Dockerfile and entrypoint
  provisioner "file" {
    source      = "${path.root}/../fargate_runner"
    destination = "/tmp/fargate_runner"
  }

  # Build and push Docker image to ECR
  provisioner "shell" {
    inline = [
      "set -e",
      "echo '==================================='",
      "echo 'Building Docker Image on ARM64'",
      "echo '==================================='",
      "",
      "# ECR login",
      "export AWS_REGION=${var.aws_region}",
      "ECR_PASSWORD=$(aws ecr get-login-password --region $AWS_REGION)",
      "echo $ECR_PASSWORD | sudo docker login --username AWS --password-stdin ${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com",
      "",
      "# Use uploaded Dockerfile",
      "cd /tmp/fargate_runner",
      "",
      "# Build image",
      "BUILD_TAG='${local.timestamp}'",
      "ECR_URL='${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${var.ecr_repository}'",
      "",
      "sudo docker build \\",
      "  --build-arg RUNNER_VERSION=${var.runner_version} \\",
      "  --build-arg RUNNER_ARCH=${var.architecture} \\",
      "  -t $ECR_URL:latest \\",
      "  -t $ECR_URL:$BUILD_TAG \\",
      "  .",
      "",
      "# Push to ECR",
      "sudo docker push $ECR_URL:latest",
      "sudo docker push $ECR_URL:$BUILD_TAG",
      "",
      "echo '✓ Docker image built and pushed to ECR'",
      "echo \"  Repository: $ECR_URL\"",
      "echo \"  Tags: latest, $BUILD_TAG\""
    ]
  }
}
