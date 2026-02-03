# VPC Endpoints for ECR access in IPv6-only environment
#
# ECR doesn't support IPv6, so we need PrivateLink endpoints
# to pull container images without IPv4 connectivity.

resource "aws_security_group" "vpc_endpoints" {
  name        = "${local.vpc_name}-endpoints-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port        = 443
    to_port          = 443
    protocol         = "tcp"
    ipv6_cidr_blocks = [aws_vpc.main.ipv6_cidr_block]
  }

  tags = merge(local.common_tags, {
    Name = "${local.vpc_name}-endpoints-sg"
  })
}

# ECR API endpoint (for ecr:* API calls)
resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${local.aws_region}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.public[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.vpc_name}-ecr-api"
  })
}

# ECR DKR endpoint (for docker pull/push)
resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${local.aws_region}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.public[*].id
  security_group_ids  = [aws_security_group.vpc_endpoints.id]
  private_dns_enabled = true

  tags = merge(local.common_tags, {
    Name = "${local.vpc_name}-ecr-dkr"
  })
}

# S3 endpoint (ECR stores layers in S3)
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${local.aws_region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = [aws_route_table.public.id]

  tags = merge(local.common_tags, {
    Name = "${local.vpc_name}-s3"
  })
}
