# 10U Labs API Infrastructure

A comprehensive AWS CDK infrastructure project that deploys a serverless API
Gateway with Lambda functions, GitHub Actions self-hosted runners, and
CloudFront distribution for api.10ulabs.com.

## Overview

This infrastructure creates a complete serverless API platform with integrated
CI/CD capabilities using GitHub Actions self-hosted runners. The system
combines API Gateway for REST endpoints, Lambda functions for serverless
compute, ECS Fargate for ephemeral GitHub runners, and CloudFront for global
content delivery.

## Key Features

- **Serverless API**: REST API with health check and echo endpoints
- **Custom Domain**: SSL-secured api.10ulabs.com with CloudFront distribution
- **GitHub Runners**: Both ECS Fargate and EC2 spot instance runners
- **Documentation**: Automated OpenAPI spec deployment and interactive docs
- **Security**: WAF protection, VPC isolation, and IAM role-based access
- **Monitoring**: CloudWatch logs and API Gateway access logging

## Resources Created

### Networking & Security

- **VPC**: Custom VPC with public subnets for runner infrastructure
- **Security Groups**: Isolated security group for GitHub runners
- **Certificate**: ACM SSL certificate for api.10ulabs.com
- **WAF**: Web Application Firewall for CloudFront protection

### API Infrastructure

- **API Gateway**: REST API with OpenAPI specification
- **Lambda Functions**: Health check, echo, and catch-all handlers
- **CloudFront**: Global CDN with API and documentation origins
- **Route53**: DNS A record for custom domain

### GitHub Runners

- **ECR Repository**: Container registry for GitHub runner images
- **ECS Cluster**: Fargate cluster for ephemeral runners
- **Task Definition**: Fargate task with GitHub token integration
- **IAM Roles**: EC2 instance profile and task execution roles

### Storage & Secrets

- **S3 Bucket**: API documentation and OpenAPI spec hosting
- **Secrets Manager**: GitHub tokens and webhook secrets
- **CloudWatch Logs**: API access logs and Lambda function logs

## Prerequisites

### Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Required packages from requirements.txt:

- `aws-cdk-lib==2.150.0` - AWS CDK framework
- `constructs>=10.0.0,<11.0.0` - CDK constructs library
- `boto3>=1.34.0` - AWS SDK for Python
- `boto3-stubs[route53,route53domains,account,organizations]>=1.34.0` - Type stubs
- `requests>=2.31.0` - HTTP library
- `types-requests>=2.31.0` - Type stubs for requests
- `pyyaml>=6.0.1` - YAML parser for OpenAPI specs
- `types-pyyaml>=6.0.12` - Type stubs for PyYAML

### System Dependencies

- **Node.js** (v16 or later) - Required for AWS CDK
- **Python 3.11** - Runtime for Lambda functions and CDK app
- **Git** - For repository operations

### AWS Prerequisites

- AWS account with appropriate permissions
- Route53 hosted zone for parent domain (10ulabs.com)
- GitHub token stored in AWS Secrets Manager
- Configured AWS credentials

## Configuration

### Main Configuration (config.json)

The `config.json` file contains all deployment settings:

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1",
    "bedrock": {
      "max_tokens_check": 4000,
      "max_tokens_generate": 16000,
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    },
    "vpc": {
      "cidr": "10.0.0.0/16",
      "max_azs": 99,
      "nat_gateways": 0
    }
  },
  "domain_names": {
    "parent": "10ulabs.com",
    "subdomain": "api.10ulabs.com"
  }
}
```

### CDK Configuration (cdk.json)

CDK-specific settings and feature flags:

```json
{
  "app": "python3 app.py",
  "context": {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "@aws-cdk/core:checkSecretUsage": true,
    "@aws-cdk/core:target-partitions": ["aws"]
  }
}
```

## Installation & Deployment

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install CDK CLI (if not already installed)
npm install -g aws-cdk
```

### 2. Configure Secrets

Create the GitHub token secret in AWS Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name "github-runner/credentials" \
  --description "GitHub token for self-hosted runners" \
  --secret-string "your-github-token"
```

### 3. Bootstrap CDK (first time only)

```bash
cdk bootstrap aws://781581267945/us-east-1
```

### 4. Deploy Infrastructure

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy the stack
cdk deploy TenULabsApi
```

### 5. Verify Deployment

Test the API endpoints:

```bash
# Health check
curl https://api.10ulabs.com/health

# Echo endpoint
curl -X POST https://api.10ulabs.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello World"}'
```

## Usage

### API Endpoints

The deployed API provides the following endpoints:

- `GET /health` - Health check endpoint
- `POST /v1/echo` - Echo service for testing
- `GET /` - API documentation (interactive Swagger UI)
- `GET /openapi.yaml` - OpenAPI specification

### GitHub Runners

#### Fargate Runners

Ephemeral runners that start on-demand:

- **Labels**: `ephemeral-ecs-fargate-spot`
- **Resources**: 256 CPU, 512MB memory
- **Use case**: Lightweight CI/CD tasks

#### EC2 Spot Runners

Cost-effective runners for longer tasks:

- **Labels**: `ephemeral-ec2-spot-instance`
- **Instance Types**: `t4g.large`, `t4g.medium`, `t4g.small`
- **Max Price**: $0.05/hour
- **Use case**: Heavy builds and testing

### Documentation Generation

The infrastructure includes a README generation system using AWS Bedrock:

```bash
# Check if README needs updating
python scripts/readme.py --check \
  --project-dir . \
  --aws-region us-east-1

# Update README automatically
python scripts/readme.py --update \
  --project-dir . \
  --aws-region us-east-1
```

## Architecture Overview

### Request Flow

1. **Client Request** → CloudFront distribution
2. **CloudFront** → Routes to appropriate origin:
   - `/health`, `/v1/*` → API Gateway
   - `/`, `/openapi.yaml` → S3 bucket
3. **API Gateway** → Lambda function execution
4. **Lambda** → Returns response via API Gateway

### GitHub Actions Integration

1. **Webhook** triggers runner provisioning
2. **ECS/EC2** provisions ephemeral runner
3. **Runner** registers with GitHub
4. **Job Execution** runs CI/CD tasks
5. **Cleanup** terminates runner after job completion

### Security Architecture

- **CloudFront** provides DDoS protection and caching
- **WAF** filters malicious requests
- **VPC** isolates runner infrastructure
- **IAM Roles** provide least-privilege access
- **Secrets Manager** secures GitHub tokens

## Security Considerations

### Network Security

- VPC with public subnets only (no private subnets for cost optimization)
- Security groups restrict runner network access
- CloudFront provides edge protection

### Access Control

- IAM roles follow principle of least privilege
- EC2 runners can only terminate instances with specific tags
- Lambda functions have minimal permissions
- Secrets are encrypted at rest and in transit

### Data Protection

- All traffic uses HTTPS/TLS encryption
- GitHub tokens stored in AWS Secrets Manager
- CloudWatch logs retention limited to reduce exposure
- S3 bucket blocks all public access

## Troubleshooting

### Common Issues

#### CDK Deployment Failures

```bash
# Check CDK version compatibility
cdk --version
npm list -g aws-cdk

# Clear CDK cache
rm -rf cdk.out/
cdk synth
```

#### Lambda Function Errors

```bash
# Check function logs
aws logs tail /aws/lambda/TenULabsApi-HealthHandler --follow

# Test function directly
aws lambda invoke \
  --function-name TenULabsApi-HealthHandler \
  --payload '{}' \
  response.json
```

#### Runner Registration Issues

```bash
# Check ECS task logs
aws ecs describe-tasks \
  --cluster TenULabsRunnerCluster \
  --tasks <task-arn>

# Verify GitHub token secret
aws secretsmanager get-secret-value \
  --secret-id github-runner/credentials
```

#### DNS Resolution Problems

```bash
# Verify CloudFront distribution
aws cloudfront get-distribution \
  --id <distribution-id>

# Check Route53 records
aws route53 list-resource-record-sets \
  --hosted-zone-id <zone-id>
```

### Monitoring and Debugging

- **CloudWatch Logs**: All Lambda functions and API Gateway logs
- **CloudWatch Metrics**: API Gateway and CloudFront metrics
- **AWS X-Ray**: Distributed tracing for Lambda functions
- **CloudFormation Events**: Stack deployment progress and errors
