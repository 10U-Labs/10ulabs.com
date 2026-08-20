# Shared VPC for Runner Compute Resources
#
# This VPC is used by:
# - ECS runners (Fargate)
# - EC2 runners

resource "aws_vpc" "main" {
  cidr_block           = local.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, {
    Name    = local.vpc_name
    Purpose = "runners"
  })
}

resource "aws_subnet" "public" {
  count = min(length(local.vpc_azs), local.vpc_max_azs)

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(local.vpc_cidr, local.public_subnet_cidr_mask - tonumber(split("/", local.vpc_cidr)[1]), count.index)
  availability_zone       = local.vpc_azs[count.index]
  map_public_ip_on_launch = true

  tags = merge(local.common_tags, {
    Name    = "${local.vpc_name}-public-${count.index + 1}"
    Purpose = "runners"
  })
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(local.common_tags, {
    Name    = "${local.vpc_name}-igw"
    Purpose = "runners"
  })
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(local.common_tags, {
    Name    = "${local.vpc_name}-public-rt"
    Purpose = "runners"
  })
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
