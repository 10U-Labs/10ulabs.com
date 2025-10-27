# GitHub Actions Self-Hosted Runners on AWS

This directory contains workflows and configurations for deploying GitHub Actions self-hosted runners on AWS infrastructure.

## Architecture

### EC2 Docker Builder (c8gd.2xlarge Spot Instance)
- **Purpose**: Building Docker images and resource-intensive tasks
- **Instance Type**: c8gd.2xlarge (ARM64)
- **Compute**: 8 vCPUs, 16 GB RAM
- **Storage**: 100 GB GP3 EBS volume with NVMe instance store
- **Cost Optimization**: EC2 Spot instance with max price $0.50/hour
- **Labels**: `docker-builder`, `ec2`, `arm64`, `spot`

### ECS Fargate General Runners (Spot)
- **Purpose**: General CI/CD tasks, testing, linting, etc.
- **Compute**: 0.5 vCPU, 1 GB RAM
- **Cost Optimization**: 80% Fargate Spot, 20% Fargate On-Demand
- **Auto-scaling**: 1-10 instances based on CPU/Memory utilization
- **Labels**: `fargate`, `general`, `spot`

## Prerequisites

### AWS Setup
1. **AWS Account**: Update `account_id` in `config/aws-runners.yaml`
2. **VPC and Subnets**: Configure VPC and subnet IDs in CloudFormation templates
3. **IAM Role**: Create `GitHubActionsRole` with OIDC provider for GitHub Actions
4. **GitHub Token**: Store as `GH_RUNNER_TOKEN` secret in repository

### GitHub Secrets Required
- `GH_RUNNER_TOKEN`: Personal Access Token with `repo` and `admin:org` scopes

### AWS IAM OIDC Provider Setup
```bash
# Create OIDC provider for GitHub Actions
aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# Create IAM role with trust policy
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_ORG/YOUR_REPO:*"
        }
      }
    }
  ]
}
EOF

aws iam create-role \
    --role-name GitHubActionsRole \
    --assume-role-policy-document file://trust-policy.json

# Attach necessary permissions
aws iam attach-role-policy \
    --role-name GitHubActionsRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonEC2FullAccess

aws iam attach-role-policy \
    --role-name GitHubActionsRole \
    --policy-arn arn:aws:iam::aws:policy/AmazonECS_FullAccess

aws iam attach-role-policy \
    --role-name GitHubActionsRole \
    --policy-arn arn:aws:iam::aws:policy/CloudFormationFullAccess
```

## Deployment

### Deploy EC2 Docker Builder
```bash
# Manual deployment
gh workflow run deploy-ec2-docker-runner.yml -f action=deploy

# Destroy
gh workflow run deploy-ec2-docker-runner.yml -f action=destroy
```

### Deploy Fargate Runners
```bash
# Deploy with default runner count (from config)
gh workflow run deploy-fargate-runners.yml -f action=deploy

# Deploy with specific runner count
gh workflow run deploy-fargate-runners.yml -f action=deploy -f runner_count=5

# Destroy
gh workflow run deploy-fargate-runners.yml -f action=destroy
```

## Usage in Workflows

### Using Docker Builder
```yaml
jobs:
  build:
    runs-on: [self-hosted, docker-builder]
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t myapp .
```

### Using Fargate Runners
```yaml
jobs:
  test:
    runs-on: [self-hosted, fargate]
    steps:
      - uses: actions/checkout@v4
      - name: Run tests
        run: npm test
```

## Cost Estimation

### EC2 Docker Builder (c8gd.2xlarge Spot)
- **Spot Price**: ~$0.25-0.35/hour (vs $0.688 on-demand)
- **Monthly Cost** (24/7): ~$180-250
- **Recommended**: Use with auto-scaling and scheduled shutdown

### Fargate Runners (0.5 vCPU, 1 GB RAM Spot)
- **Spot Price**: ~$0.01-0.015/hour per runner
- **Monthly Cost** (2 runners 24/7): ~$15-20
- **Auto-scaling**: Cost scales with usage

## Monitoring

### CloudWatch Logs
- EC2 Runner: Instance logs via SSM and CloudWatch Agent
- Fargate Runners: `/ecs/github-runners-fargate` log group

### ECS Service Metrics
```bash
aws ecs describe-services \
    --cluster github-runners-fargate \
    --services github-runners-fargate \
    --region us-east-1
```

### Runner Status
Check active runners at:
`https://github.com/YOUR_ORG/YOUR_REPO/settings/actions/runners`

## Troubleshooting

### Runner not appearing in GitHub
1. Check CloudFormation stack status
2. Verify GitHub token has correct permissions
3. Check CloudWatch logs for errors
4. Ensure security groups allow outbound HTTPS

### Fargate tasks failing to start
1. Verify ECR image exists and is accessible
2. Check VPC and subnet configuration
3. Verify secrets are properly configured
4. Check task execution role permissions

### EC2 spot instance terminated
1. Spot instances can be interrupted with 2-minute notice
2. Consider increasing max price in CloudFormation
3. Implement graceful shutdown handling
4. Use multiple instance types for better availability

## Security Considerations

- ✅ Runners use IAM roles with minimal permissions
- ✅ GitHub tokens stored in AWS Secrets Manager
- ✅ Runners are ephemeral and cleaned up after each job
- ✅ Private subnets with NAT gateway for internet access
- ✅ Security groups restrict inbound traffic
- ⚠️ Update VPC and subnet IDs before deployment
- ⚠️ Rotate GitHub tokens regularly
- ⚠️ Review IAM permissions periodically

## Maintenance

### Update Runner Version
1. Update `RUNNER_VERSION` in workflows
2. Rebuild Fargate image
3. Update EC2 UserData in CloudFormation

### Scale Runners
Update `config/aws-runners.yaml` and push to main branch:
```yaml
fargate_runners:
  min_instances: 2
  max_instances: 20
```

## Additional Resources

- [GitHub Actions Self-Hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [AWS ECS Fargate Spot](https://aws.amazon.com/fargate/pricing/)
- [AWS EC2 Spot Instances](https://aws.amazon.com/ec2/spot/)
