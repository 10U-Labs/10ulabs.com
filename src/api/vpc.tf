locals {
  azs = slice(data.aws_availability_zones.available.names, 0, var.vpc_max_azs)
}

data "aws_availability_zones" "available" {
  state = "available"
}

resource "aws_vpc" "runner_vpc" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name    = var.vpc_name
    Purpose = "10ulabs-api-and-runners"
  }
}

resource "aws_subnet" "public" {
  count = min(length(local.azs), var.vpc_max_azs)

  vpc_id                  = aws_vpc.runner_vpc.id
  cidr_block              = cidrsubnet(var.vpc_cidr, var.public_subnet_cidr_mask - tonumber(split("/", var.vpc_cidr)[1]), count.index)
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.vpc_name}-public-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.runner_vpc.id

  tags = {
    Name = "${var.vpc_name}-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.runner_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.vpc_name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "runner_sg" {
  name        = "self-hosted-runner-sg"
  description = "Security group for GitHub self-hosted runner Fargate tasks"
  vpc_id      = aws_vpc.runner_vpc.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "self-hosted-runner-sg"
  }
}
