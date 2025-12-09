# Shared VPC for Compute Resources
#
# This VPC is used by:
# - ECS runners (Fargate)
# - EC2 runners
# - Any other compute resources that need internet access

locals {
  vpc_name                = "${local.resource_prefix}Vpc"
  vpc_cidr                = "10.0.0.0/16"
  vpc_max_azs             = 99
  public_subnet_cidr_mask = 24
  vpc_azs                 = slice(data.aws_availability_zones.available.names, 0, min(length(data.aws_availability_zones.available.names), local.vpc_max_azs))
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "main" {
  cidr_block           = local.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name      = local.vpc_name
    ManagedBy = "terraform"
    Purpose   = "shared-compute"
  }
}

resource "aws_subnet" "public" {
  count = min(length(local.vpc_azs), local.vpc_max_azs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(local.vpc_cidr, local.public_subnet_cidr_mask - tonumber(split("/", local.vpc_cidr)[1]), count.index)
  availability_zone       = local.vpc_azs[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name      = "${local.vpc_name}-public-${count.index + 1}"
    ManagedBy = "terraform"
    Purpose   = "shared-compute"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name      = "${local.vpc_name}-igw"
    ManagedBy = "terraform"
    Purpose   = "shared-compute"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name      = "${local.vpc_name}-public-rt"
    ManagedBy = "terraform"
    Purpose   = "shared-compute"
  }
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Security Group for GitHub Self-Hosted Runners
# Used by both ECS (Fargate) and EC2 runners
resource "aws_security_group" "runner" {
  name        = "self-hosted-runner-sg"
  description = "Security group for GitHub self-hosted runners (ECS/EC2)"
  vpc_id      = aws_vpc.main.id

  # Egress-only - runners need outbound internet access
  # No inbound rules needed as runners initiate all connections
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name      = "self-hosted-runner-sg"
    ManagedBy = "terraform"
    Purpose   = "runners"
  }
}
