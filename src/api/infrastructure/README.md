# 10U Labs API Infrastructure

AWS CDK infrastructure for the 10U Labs API Gateway, supporting both API
endpoints and GitHub self-hosted runners on ECS Fargate and EC2 Spot
instances.

## Overview

This infrastructure deploys a comprehensive API platform for `api.10ulabs.com`
that combines API Gateway endpoints with GitHub self-hosted runner
infrastructure. It provides a scalable, serverless API backend with integrated
CI/CD capabilities using containerized runners.

## Key Features

- **API Gateway**: RESTful API with custom domain and SSL certificate
- **Lambda Functions**: Health checks, echo endpoints, and catch-all handlers
- **CloudFront Distribution**: Global CDN with API documentation hosting
- **GitHub Runners**: Self-hosted runners on ECS Fargate and EC2 Spot instances
- **Security**: WAF protection, VPC isolation, and IAM role-based access
- **Monitoring**: CloudWatch logs and metrics for all components
- **Documentation**: Automated deployment of OpenAPI specifications

## AWS Resources Created

### Networking

- **VPC**: Custom VPC with public subnets for runner infrastructure
- **Security Groups**: Isolated network access for runner tasks
- **Route 53**: DNS records for custom domain routing

### Compute & Containers

- **ECS Cluster**: Fargate cluster for containerized GitHub runners
- **ECR Repository**: Container registry for runner images
- **ECS Task Definition**: Fargate task configuration with GitHub token secrets
- **EC2 IAM Roles**: Instance profiles for EC2 Spot runner instances

### API & Web Services

- **API Gateway**: REST API with OpenAPI specification integration
- **Lambda Functions**: Python 3.11 functions for API endpoints
- **CloudFront**: Global CDN with S3 origin for documentation
- **S3 Bucket**: Static website hosting for API documentation
- **WAF**: Web Application Firewall for DDoS and attack protection

### Security & Secrets

- **Certificate Manager**: SSL/TLS certificates for HTTPS
- **Secrets Manager**: GitHub tokens and webhook secrets
- **IAM Roles**: Service-specific roles with least privilege access

### Monitoring & Logging

- **CloudWatch Logs**: Centralized logging for all services
- **API Gateway Logs**: Request/response logging and metrics

## Prerequisites

### System Dependencies

- **Node.js** (version 18 or later) - Required for AWS CDK CLI
- **Python** (version 3.11 or later) - Runtime for CDK application
- **Git** - For repository operations and deployments

### Python Dependencies

Install the required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

**Required packages:**

- `aws-cdk-lib==2.150.0` - AWS CDK framework
- `constructs>=10.0.0,<11.0.0` - CDK construct library
- `boto3>=1.34.0` - AWS SDK for Python
- `boto3-stubs[route53,route53domains,account,organizations]>=1.34.0` - Type stubs
- `requests>=2.31.0` - HTTP client library
- `types-requests>=2.31.0` - Type stubs for requests
- `pyyaml>=6.0.1` - YAML parser for OpenAPI specs
- `types-pyyaml>=6.0.12` - Type stubs for PyYAML

### AWS Prerequisites

- **AWS Account**: Valid AWS account with appropriate permissions
- **Parent Domain**: Existing Route 53 hosted zone for the parent domain
- **GitHub Token**: Personal access token stored in AWS Secrets Manager

## Configuration

### Main Configuration (`config.json`)

The infrastructure uses a comprehensive configuration file:

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1",
    "vpc": {
      "cidr": "10.0.0.0/16",
      "max_azs": 99,
      "nat_gateways": 0
    },
    "fargate_runners": {
      "cpu": "256",
      "memory": "512",
      "runner_labels": ["ephemeral-ecs-fargate-spot"]
    }
  },
  "domain_names": {
    "parent": "10ulabs.com",
    "subdomain": "api.10ulabs.com"
  }
}
```

### CDK Configuration (`cdk.json`)

```json
{
  "app": "python3 app.py",
  "context": {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "@aws-cdk/core:checkSecretUsage": true
  }
}
```

## Installation & Deployment

### 1. Install Dependencies

```bash
# Install Node.js dependencies for CDK
npm install -g aws-cdk

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure AWS Credentials

Ensure your AWS credentials are configured for the target account:

```bash
# Configure default profile or use environment variables
export AWS_PROFILE=your-profile-name
export AWS_REGION=us-east-1
```

### 3. Prepare Secrets

Create the GitHub token secret in AWS Secrets Manager:

```bash
# The secret should be created with the name specified in config.json
# Default: "github-runner/credentials"
```

### 4. Deploy Infrastructure

```bash
# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy the stack
cdk deploy TenULabsApi

# View deployment outputs
cdk deploy --outputs-file outputs.json
```

### 5. Verify Deployment

Test the deployed API endpoints:

```bash
# Health check
curl https://api.10ulabs.com/health

# Echo endpoint
curl -X POST https://api.10ulabs.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

## Usage

### API Endpoints

The deployed API provides several endpoints:

- `GET /health` - Health check endpoint
- `POST /v1/echo` - Echo service for testing
- `GET /` - API documentation (served from S3)
- `GET /openapi.yaml` - OpenAPI specification

### GitHub Runners

The infrastructure supports two types of self-hosted runners:

**ECS Fargate Runners:**

- Ephemeral containers with labels: `ephemeral-ecs-fargate-spot`
- Automatically scale based on GitHub webhook events
- 256 CPU units, 512 MB memory per task

**EC2 Spot Runners:**

- Spot instances with labels: `ephemeral-ec2-spot-instance`
- Cost-effective for longer-running jobs
- Instance types: `t4g.large`, `t4g.medium`, `t4g.small`

### Accessing Resources

Use the CDK outputs to integrate with other services:

```bash
# Get API Gateway REST API ID
aws cloudformation describe-stacks \
  --stack-name TenULabsApi \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayRestApiId`].OutputValue' \
  --output text

# Get VPC ID for runner integration
aws cloudformation describe-stacks \
  --stack-name TenULabsApi \
  --query 'Stacks[0].Outputs[?OutputKey==`VpcId`].OutputValue' \
  --output text
```

## Architecture

### Request Flow

1. **Client Request** → CloudFront Distribution
2. **CloudFront** → API Gateway (for `/health`, `/v1/*`) or S3 (for docs)
3. **API Gateway** → Lambda Functions
4. **Lambda Functions** → Process and return response

### GitHub Runner Flow

1. **GitHub Webhook** → Webhook Handler Lambda
2. **Webhook Handler** → ECS/EC2 Runner Creation
3. **Runner** → Connects to GitHub and executes jobs
4. **Job Completion** → Runner self-terminates

### Security Architecture

- **WAF**: Protects CloudFront distribution from common attacks
- **VPC**: Isolates runner infrastructure in private networking
- **IAM Roles**: Least privilege access for all services
- **Secrets Manager**: Secure storage for GitHub tokens and webhook secrets

## Security Considerations

### Network Security

- Runners operate in isolated VPC with controlled egress
- Security groups restrict network access to required ports only
- No NAT gateways reduce attack surface and costs

### Access Control

- IAM roles follow principle of least privilege
- EC2 runners can only terminate instances they manage
- GitHub tokens stored securely in AWS Secrets Manager

### API Security

- WAF provides DDoS protection and request filtering
- API Gateway throttling prevents abuse
- CloudFront provides additional layer of protection

## Troubleshooting

### Common Issues

**CDK Bootstrap Errors:**

```bash
# Ensure you have the correct permissions and region
cdk bootstrap --profile your-profile
```

**Domain Certificate Issues:**

- Verify the parent hosted zone exists and is properly configured
- Check that DNS validation records are created automatically

**Runner Connection Issues:**

- Verify GitHub token has correct repository permissions
- Check ECS task logs for authentication failures
- Ensure ECR repository contains valid runner image

### Debugging Commands

```bash
# View CDK differences before deploy
cdk diff

# Check CloudFormation events
aws cloudformation describe-stack-events --stack-name TenULabsApi

# View Lambda function logs
aws logs tail /aws/lambda/TenULabsApi-HealthHandler --follow

# Check ECS task status
aws ecs list-tasks --cluster TenULabsRunnerCluster
```

### Log Locations

- **API Gateway**: CloudWatch Logs group created automatically
- **Lambda Functions**: `/aws/lambda/function-name`
- **ECS Tasks**: `/ecs/github-runner`
- **CloudFront**: Access logs (if enabled)

For additional support, check the CloudFormation stack events and resource
status in the AWS Console.
