# 10U Labs API Infrastructure

A comprehensive AWS infrastructure project that deploys a serverless API Gateway
with Lambda functions and GitHub self-hosted runners using AWS CDK (Python).
This infrastructure powers api.10ulabs.com and provides container-based CI/CD
capabilities with both Fargate and EC2 runners.

## Overview

This project creates a complete cloud infrastructure for hosting APIs and
managing GitHub Actions self-hosted runners. It includes a REST API with
health check and echo endpoints, containerized GitHub runners on ECS Fargate,
and optional EC2 spot instance runners for cost-effective CI/CD workloads.

## Key Features

- **Serverless API**: AWS Lambda-powered REST API with custom domain
- **Container Registry**: Private ECR repository for runner images
- **ECS Fargate Runners**: Ephemeral containerized GitHub Actions runners
- **EC2 Spot Runners**: Cost-effective virtual machine runners
- **SSL/TLS**: Automatic certificate management with Route 53 validation
- **Security**: IAM roles, security groups, and secrets management
- **Monitoring**: CloudWatch logs and API Gateway access logging
- **Infrastructure as Code**: Complete AWS CDK implementation in Python

## AWS Resources Created

### Networking & Security

- **VPC**: Custom virtual private cloud with public subnets
- **Security Groups**: Configured for outbound internet access
- **SSL Certificate**: ACM certificate with DNS validation
- **Route 53 Records**: A record for custom domain routing

### API Infrastructure

- **API Gateway**: REST API with custom domain and CORS
- **Lambda Function**: Python 3.11 runtime for API endpoints
- **CloudWatch Logs**: API access logs and Lambda function logs

### Container Infrastructure

- **ECR Repository**: Private Docker image registry with lifecycle policies
- **ECS Cluster**: Fargate cluster with container insights
- **Task Definition**: Fargate task for GitHub runner containers
- **CloudWatch Logs**: Container logging with one-week retention

### IAM & Secrets

- **IAM Roles**: Separate roles for Lambda, ECS tasks, and EC2 instances
- **Instance Profile**: EC2 profile for spot instance runners
- **Secrets Manager**: GitHub tokens and webhook secrets
- **Policies**: Fine-grained permissions for each service

## Prerequisites

### System Dependencies

- **Python 3.11+**: Required for AWS CDK and Lambda runtime
- **Node.js 18+**: Required for AWS CDK CLI
- **Git**: For repository management and deployments

### Python Dependencies

Install the required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

**Required packages:**

- `aws-cdk-lib==2.150.0` - AWS CDK core library
- `constructs>=10.0.0,<11.0.0` - CDK constructs framework
- `boto3>=1.34.0` - AWS SDK for Python
- `boto3-stubs[route53,route53domains,account,organizations]>=1.34.0` - Type hints
- `requests>=2.31.0` - HTTP library for API validation
- `types-requests>=2.31.0` - Type hints for requests

### AWS Prerequisites

- **AWS Account**: Valid AWS account with appropriate permissions
- **Route 53 Hosted Zone**: Existing hosted zone for parent domain
- **GitHub Token**: Personal access token stored in AWS Secrets Manager

## Configuration

### config.json

The main configuration file defines AWS settings, domain names, and resource
parameters:

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1"
  },
  "domain_names": {
    "parent": "10ulabs.com",
    "subdomain": "api.10ulabs.com"
  }
}
```

**Key configuration sections:**

- `aws.bedrock`: AI/ML model settings for future features
- `aws.vpc`: Network configuration with CIDR blocks and subnets
- `aws.fargate_runners`: ECS Fargate task specifications
- `aws.ec2_runners`: EC2 spot instance configuration
- `naming`: Consistent naming convention for all resources
- `lambda`: Function timeout and memory settings
- `github`: Organization and repository settings

### cdk.json

CDK framework configuration with feature flags and context settings:

```json
{
  "app": "python3 app.py",
  "watch": {
    "include": ["**"],
    "exclude": ["README.md", "cdk*.json", "**/__pycache__"]
  }
}
```

## Installation and Deployment

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install AWS CDK CLI (if not already installed)
npm install -g aws-cdk
```

### 2. Configure AWS Credentials

Ensure your AWS credentials are configured with appropriate permissions:

```bash
# Configure AWS credentials (choose one method)
export AWS_PROFILE=your-profile-name
# OR set environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_DEFAULT_REGION=us-east-1
```

### 3. Bootstrap CDK (First-time setup)

```bash
cdk bootstrap
```

### 4. Deploy Infrastructure

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy the stack
cdk deploy TenULabsApi
```

### 5. Verify API Deployment

Use the included validation script to confirm the API is accessible:

```bash
python3 poll_api_until_it_has_propagated.py https://api.10ulabs.com
```

## Usage

### API Endpoints

After deployment, the following endpoints are available:

- **Health Check**: `GET https://api.10ulabs.com/health`
- **Echo Service**: `POST https://api.10ulabs.com/v1/echo`

#### Health Check Example

```bash
curl -X GET https://api.10ulabs.com/health
```

Response:

```json
{
  "status": "healthy",
  "service": "10U Labs API",
  "version": "1.0.0"
}
```

#### Echo Service Example

```bash
curl -X POST https://api.10ulabs.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, World!"}'
```

Response:

```json
{
  "echo": {"message": "Hello, World!"},
  "received_at": "request-id-here"
}
```

### GitHub Runners

#### Fargate Runners

Ephemeral containers that spin up for individual job runs:

- **Labels**: `ephemeral-ecs-fargate-spot`
- **Resources**: 256 CPU units, 512 MB memory
- **Lifecycle**: Automatic cleanup after job completion

#### EC2 Runners

Spot instances for longer-running or resource-intensive jobs:

- **Labels**: `ephemeral-ec2-spot-instance`
- **Instance Types**: t4g.large, t4g.medium, t4g.small
- **Max Price**: $0.05 per hour

### Container Image Management

Build and push runner images to the ECR repository:

```bash
# Get ECR login token
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  781581267945.dkr.ecr.us-east-1.amazonaws.com

# Build and push image
docker build -t github-runner .
docker tag github-runner:latest \
  781581267945.dkr.ecr.us-east-1.amazonaws.com/github-runner:latest
docker push 781581267945.dkr.ecr.us-east-1.amazonaws.com/github-runner:latest
```

## Architecture

### Component Interaction

```text
Internet → Route 53 → API Gateway → Lambda Function
                                 ↓
GitHub Webhooks → Secrets Manager ← ECS Fargate Tasks
                                 ↓
                              ECR Repository
                                 ↓
                           VPC with Public Subnets
```

### Data Flow

1. **API Requests**: Route 53 routes traffic to API Gateway
2. **Lambda Processing**: API Gateway invokes Lambda for request handling
3. **GitHub Integration**: Webhooks trigger runner provisioning
4. **Container Deployment**: ECS pulls images from ECR and runs tasks
5. **Logging**: All components send logs to CloudWatch

### Authentication & Authorization

- **API Gateway**: Open endpoints with CORS support
- **ECS Tasks**: IAM roles for AWS service access
- **GitHub Integration**: Personal access tokens in Secrets Manager
- **ECR Access**: IAM policies for image pull/push operations

## Security Considerations

### Network Security

- **VPC Isolation**: Dedicated VPC with controlled subnet access
- **Security Groups**: Outbound-only rules for runner connectivity
- **No NAT Gateway**: Cost optimization using public subnets only

### Identity & Access Management

- **Principle of Least Privilege**: Minimal IAM permissions per service
- **Role-based Access**: Separate roles for different resource types
- **Resource Tagging**: Consistent tagging for access control

### Secrets Management

- **AWS Secrets Manager**: Encrypted storage for sensitive data
- **Automatic Rotation**: Webhook secrets with secure generation
- **Environment Variables**: Secure injection into container tasks

### API Security

- **HTTPS Only**: TLS encryption for all API communications
- **CORS Configuration**: Controlled cross-origin access
- **Input Validation**: JSON parsing with error handling

## Troubleshooting

### Common Issues

#### CDK Bootstrap Errors

```bash
# If bootstrap fails, check AWS credentials and permissions
cdk doctor
aws sts get-caller-identity
```

#### Domain Validation Issues

Ensure the parent hosted zone exists and is accessible:

```bash
# Verify hosted zone
aws route53 list-hosted-zones-by-name --dns-name 10ulabs.com
```

#### ECR Authentication Failures

Update Docker credentials for ECR access:

```bash
# Refresh ECR login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  781581267945.dkr.ecr.us-east-1.amazonaws.com
```

#### Task Definition Issues

Check ECS task logs for container startup problems:

```bash
# View ECS cluster status
aws ecs describe-clusters --clusters TenULabsRunnerCluster

# Check task definitions
aws ecs list-task-definitions --family-prefix github-runner
```

### Monitoring and Debugging

#### CloudWatch Logs

- **API Gateway**: `/aws/apigateway/TenULabsApi`
- **Lambda Function**: `/aws/lambda/TenULabsApi-ApiHandler`
- **ECS Tasks**: `/aws/ecs/github-runner`

#### API Validation

Use the polling script to verify API propagation:

```bash
# Test with custom endpoint
python3 poll_api_until_it_has_propagated.py \
  https://api.10ulabs.com --max-attempts 15
```

#### Infrastructure Validation

```bash
# Check stack status
cdk list
cdk diff TenULabsApi

# Verify outputs
aws cloudformation describe-stacks \
  --stack-name TenULabsApi \
  --query 'Stacks[0].Outputs'
```
