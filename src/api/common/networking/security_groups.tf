# Security Group for GitHub Self-Hosted Runners
#
# Used by both ECS (Fargate) and EC2 runners.
# Egress-only - runners need outbound internet access but no inbound rules
# as runners initiate all connections.

resource "aws_security_group" "runner" {
  name        = "self-hosted-runner-sg"
  description = "Security group for GitHub self-hosted runners (ECS/EC2)"
  vpc_id      = aws_vpc.main.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name    = "self-hosted-runner-sg"
    Purpose = "runners"
  })
}
