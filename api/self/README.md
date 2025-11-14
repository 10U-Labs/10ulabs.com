# 10U Labs API Infrastructure

A serverless API infrastructure built with AWS CDK that deploys a REST API
using API Gateway and Lambda, with custom domain support and GitHub
self-hosted runner capabilities.

## Overview

This infrastructure creates a production-ready serverless API with custom
domain support, SSL/TLS encryption, and comprehensive logging. The stack
also provisions resources for GitHub self-hosted runners using both ECS
Fargate and EC2 instances.

## Key Features

- **Serverless Architecture**: API Gateway + Lambda for scalable,
  cost-effective API hosting
- **Custom Domain**: SSL/TLS certificate with Route53 DNS configuration
- **CORS Enabled**: Cross-origin resource sharing for web applications
- **Comprehensive Logging**: CloudWatch logs for API access and Lambda
  execution
- **GitHub Integration**: Self-hosted runner infrastructure with ECR
  repository and ECS cluster
- **Security**: IAM roles, security groups, and secrets management

## Resources Created

### Core API Infrastructure

- **API Gateway REST API**: Main API endpoint with custom domain support
- **Lambda Function**: Python 3.11 runtime handling API requests
- **ACM Certificate**: SSL/TLS certificate for HTTPS endpoints
- **Route53 A Record**: DNS alias record pointing to API Gateway
- **CloudWatch Log Groups**: API access logs and Lambda execution logs

### GitHub Runner Infrastructure

- **VPC**: Isolated network with public subnets for runner instances
- **ECS Cluster**: Fargate cluster for containerized GitHub runners
- **ECR Repository**: Docker image storage for runner containers
- **ECS Task Definition**: Fargate task configuration with GitHub token
- **IAM Roles**: EC2 instance profile and task execution roles
- **Security Groups**: Network access control for runner instances
- **Secrets Manager**: GitHub token and webhook secret storage

## Prerequisites

- AWS CLI configured with appropriate permissions
- AWS CDK v2 installed (`npm install -g aws-cdk`)
- Python 3.8+ with pip
- A Route53 hosted zone for your parent domain
- GitHub personal access token stored in AWS Secrets Manager

## Required AWS Permissions

Your AWS credentials need permissions for:

- API Gateway (create, update, delete)
- Lambda (create, update, delete functions)
- IAM (create roles and policies)
- Route53 (create DNS records)
- Certificate Manager (request certificates)
- CloudWatch Logs (create log groups)
- VPC, ECS, ECR (for runner infrastructure)
- Secrets Manager (create and read secrets)

## API Endpoints

### GET /health

Health check endpoint returning service status.

**Response:**

```json
{
  "status": "healthy",
  "service": "10U Labs API",
  "version": "1.0.0"
}
```

### POST /v1/echo

Echo endpoint that returns the posted JSON data.

**Request Body:**

```json
{
  "message": "Hello, World!",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Response:**

```json
{
  "echo": {
    "message": "Hello, World!",
    "timestamp": "2024-01-01T00:00:00Z"
  },
  "received_at": "aws-request-id-here"
}
```

## Configuration

The stack requires a configuration dictionary with the following structure:

```python
config = {
    "domain_names": {
        "parent": "example.com",
        "subdomain": "api.example.com"
    },
    "naming": {
        "vpc_name": "10ulabs-vpc",
        "cluster_name": "github-runners",
        "github_token_secret_name": "github-token",
        "webhook_secret_name": "github-webhook-secret"
    },
    "aws": {
        "vpc": {
            "cidr": "10.0.0.0/16",
            "max_azs": 2,
            "nat_gateways": 0
        }
    },
    "github": {
        "repo": "owner/repository"
    }
}
```

## Deployment Instructions

1. **Clone the repository and install dependencies:**

   ```bash
   git clone <repository-url>
   cd <repository-name>
   pip install -r requirements.txt
   ```

2. **Create your configuration file:**

   ```bash
   cp config.example.py config.py
   # Edit config.py with your domain and settings
   ```

3. **Bootstrap CDK (if first time in this AWS account/region):**

   ```bash
   cdk bootstrap
   ```

4. **Store GitHub token in Secrets Manager:**

   ```bash
   aws secretsmanager create-secret \
     --name "github-token" \
     --description "GitHub personal access token" \
     --secret-string "your-github-token-here"
   ```

5. **Deploy the stack:**

   ```bash
   cdk deploy ApiStack
   ```

6. **Note the outputs:**

   The deployment will output important values including:

- API Gateway URL
- Custom domain name
- VPC and subnet IDs
- ECR repository URI

## Testing the API

After deployment, test the endpoints:

```bash
# Test health endpoint
curl https://api.example.com/health

# Test echo endpoint
curl -X POST https://api.example.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello from API!"}'
```

## Architecture Notes

### Serverless Design

The API uses a serverless architecture with API Gateway handling HTTP
requests and routing them to a single Lambda function. This approach
provides:

- **Auto-scaling**: Handles traffic spikes automatically
- **Cost efficiency**: Pay only for actual requests
- **Zero maintenance**: No server management required

### Security Features

- **HTTPS Only**: All traffic encrypted with ACM certificate
- **CORS Enabled**: Configured for cross-origin web requests
- **IAM Integration**: API Gateway uses IAM for authentication (when enabled)
- **VPC Isolation**: Runner infrastructure isolated in dedicated VPC

### Monitoring and Logging

- **API Access Logs**: All requests logged to CloudWatch
- **Lambda Execution Logs**: Function execution details and errors
- **Retention Policies**: Automatic log cleanup (1 week to 1 month)

### GitHub Runner Integration

The infrastructure supports both Fargate and EC2 based GitHub self-hosted
runners:

- **Fargate Runners**: Containerized, fully managed compute
- **EC2 Runners**: Traditional instances with custom AMIs
- **Shared Resources**: VPC, security groups, and secrets

## Outputs and Integration

The stack exports numerous CloudFormation outputs for integration with
other stacks:

- API Gateway IDs for adding new routes
- VPC and subnet IDs for additional resources
- Security group IDs for network access
- ECR repository details for container builds

These exports enable modular infrastructure deployment and cross-stack
resource sharing.
