# 10U Labs API Infrastructure

A serverless API infrastructure built with AWS CDK that creates a REST API with
Lambda backend, custom domain, SSL certificate, and comprehensive monitoring.

## Overview

This infrastructure creates a production-ready serverless API using AWS API
Gateway and Lambda functions. The API is deployed with a custom domain name,
SSL/TLS encryption, CORS support, and comprehensive logging for monitoring
and debugging.

## Key Features

- **Serverless Architecture**: Built on AWS Lambda and API Gateway for
  automatic scaling and cost optimization
- **Custom Domain**: SSL-enabled custom domain with automatic certificate
  management
- **CORS Enabled**: Cross-origin resource sharing configured for web
  applications
- **Comprehensive Logging**: CloudWatch integration for API Gateway access
  logs and Lambda function logs
- **Health Monitoring**: Built-in health check endpoint for service monitoring
- **Versioned API**: Structured with `/v1` prefix for API versioning

## AWS Resources Created

### Core API Infrastructure

- **API Gateway REST API**: Main API endpoint with custom domain configuration
- **Lambda Function**: Python 3.11 runtime handling all API requests
- **ACM Certificate**: SSL/TLS certificate for HTTPS encryption
- **Route53 A Record**: DNS alias record pointing to the API Gateway
- **CloudWatch Log Groups**: Separate log groups for API access logs and
  Lambda execution logs

### Supporting Infrastructure

- **VPC**: Isolated network environment for additional services
- **ECR Repository**: Container registry for GitHub runner images
- **ECS Cluster**: Container orchestration for self-hosted GitHub runners
- **IAM Roles**: Service roles for EC2 instances and container tasks
- **Secrets Manager**: Secure storage for GitHub tokens and webhook secrets
- **Security Groups**: Network access controls for container services

## Prerequisites

- AWS CDK v2.x installed and configured
- Python 3.8 or higher
- AWS CLI configured with appropriate permissions
- Existing Route53 hosted zone for the parent domain
- GitHub token stored in AWS Secrets Manager

### Required AWS Permissions

- Route53 (DNS management)
- Certificate Manager (SSL certificates)
- API Gateway (API creation and management)
- Lambda (function deployment)
- CloudWatch Logs (logging configuration)
- IAM (role and policy management)

## API Endpoints

### GET /health

Health check endpoint that returns the service status.

**Response:**

```json
{
  "status": "healthy",
  "service": "10U Labs API",
  "version": "1.0.0"
}
```

### POST /v1/echo

Echo endpoint that returns the submitted JSON payload.

**Request Body:**

```json
{
  "message": "Hello, World!",
  "data": ["any", "json", "structure"]
}
```

**Response:**

```json
{
  "echo": {
    "message": "Hello, World!",
    "data": ["any", "json", "structure"]
  },
  "received_at": "request-id-from-lambda-context"
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
        "vpc_name": "api-vpc",
        "cluster_name": "runners-cluster",
        "task_family": "github-runner",
        "container_name": "runner",
        "log_stream_prefix": "runner",
        "github_token_secret_name": "github-token",
        "webhook_secret_name": "github-webhook-secret"
    },
    "aws": {
        "vpc": {
            "cidr": "10.0.0.0/16",
            "max_azs": 2,
            "nat_gateways": 1,
            "subnet_configuration": {
                "public_subnet_cidr_mask": 24
            }
        }
    },
    "github": {
        "repo": "organization/repository"
    }
}
```

## Deployment Instructions

### 1. Clone and Setup

```bash
git clone <repository-url>
cd <repository-directory>
pip install -r requirements.txt
```

### 2. Configure Environment

Create your configuration file or update the existing configuration with your
domain names and GitHub repository details.

### 3. Deploy Infrastructure

```bash
# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy the stack
cdk deploy ApiStack
```

### 4. Verify Deployment

After deployment completes, test the API endpoints:

```bash
# Health check
curl https://api.yourdomain.com/health

# Echo endpoint
curl -X POST https://api.yourdomain.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"test": "message"}'
```

## Testing the API

### Local Testing

Use the AWS CLI to test Lambda functions locally:

```bash
aws lambda invoke --function-name <function-name> \
  --payload '{"path":"/health","httpMethod":"GET"}' \
  response.json
```

### Integration Testing

Test the deployed API using curl or your preferred HTTP client:

```bash
# Test health endpoint
curl -v https://api.yourdomain.com/health

# Test echo endpoint with sample data
curl -X POST https://api.yourdomain.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"timestamp": "2024-01-01T00:00:00Z", "message": "test"}'

# Test CORS preflight
curl -X OPTIONS https://api.yourdomain.com/v1/echo \
  -H "Origin: https://example.com" \
  -H "Access-Control-Request-Method: POST"
```

## Architecture Notes

### Serverless Design

The API uses a serverless architecture with automatic scaling based on
request volume. Lambda functions are stateless and handle requests
independently, ensuring high availability and cost efficiency.

### Security Features

- **HTTPS Only**: All API traffic is encrypted using SSL/TLS certificates
- **CORS Configuration**: Cross-origin requests are properly handled
- **IAM Integration**: Fine-grained permissions for AWS service access
- **VPC Isolation**: Supporting services run in an isolated network

### Monitoring and Logging

- **CloudWatch Integration**: All API requests and Lambda executions are logged
- **Access Logging**: Detailed request/response logging for debugging
- **Health Monitoring**: Built-in health check for service monitoring
- **Log Retention**: Configurable retention periods for cost optimization

### Extensibility

The infrastructure is designed for easy extension:

- **Versioned Routes**: `/v1` prefix allows for API evolution
- **Modular Lambda**: Single handler can route to multiple functions
- **Export Values**: Stack outputs enable integration with other stacks
- **Resource Tagging**: Consistent tagging for resource management