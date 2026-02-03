# Security Group for GitHub Self-Hosted Runners
#
# Used by both ECS (Fargate) and EC2 runners.
# Egress-only - runners need outbound internet access but no inbound rules
# as runners initiate all connections.

resource "aws_security_group" "runner" {
  name        = "self-hosted-runner-sg"
  description = "Security group for GitHub self-hosted runners (ECS/EC2)"
  vpc_id      = aws_vpc.main.id

  # IPv6 egress to internet (GitHub, package repos, etc.)
  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    ipv6_cidr_blocks = ["::/0"]
  }

  # IPv4 egress within VPC for VPC endpoints (ECR, S3)
  # VPC endpoints use IPv4 private addresses even in IPv6-enabled subnets
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [local.vpc_cidr]
  }

  tags = merge(local.common_tags, {
    Name    = "self-hosted-runner-sg"
    Purpose = "runners"
  })
}
