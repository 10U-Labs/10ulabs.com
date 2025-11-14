# 10U Labs API Infrastructure

A serverless AWS infrastructure stack that creates a REST API with Lambda backend,
custom domain support, and integrated GitHub self-hosted runner infrastructure.

## Overview

This AWS CDK stack deploys a complete serverless API solution with the following
key components:

- **API Gateway REST API** with custom domain and SSL/TLS certificate
- **Lambda function** handling API requests with CORS support
- **Route53 DNS** configuration for custom subdomain
- **CloudWatch logging** for API access and Lambda execution
- **ECS Fargate infrastructure** for GitHub self-hosted runners
- **VPC and networking** components for secure container execution

## Key Features

- ✅ **Serverless Architecture** - No server management required
- ✅ **Custom Domain** - Professional API endpoints with SSL/TLS
- ✅ **CORS Enabled** - Ready for web application integration
- ✅ **Access Logging** - Complete request/response logging
- ✅ **Health Monitoring** - Built-in health check endpoint
- ✅ **Scalable** - Automatic scaling based on demand
- ✅ **Secure** - SSL/TLS encryption and IAM-based access control

## Resources Created

### API Gateway Components

- **REST API** (`TenULabsApi`) - Main API Gateway with custom domain
- **Custom Domain** - SSL/TLS certificate from ACM with Route53 validation
- **API Stages** - Production stage with access logging enabled
- **CORS Configuration** - Cross-origin resource sharing for all origins

### Lambda Function

- **API Handler** (`ApiHandler`) - Python 3.11 runtime with 30-second timeout
- **CloudWatch Logs** - One week retention for Lambda execution logs
- **IAM Role** - Automatically created with basic execution permissions

### Networking & DNS

- **Route53 A Record** - Alias record pointing to API Gateway
- **ACM Certificate** - Automatic SSL/TLS certificate with DNS validation
- **VPC** - Custom VPC with public subnets for runner infrastructure

### Infrastructure Support

- **ECS Cluster** - Container orchestration for GitHub runners
- **ECR Repository** - Docker image storage with lifecycle policies
- **Secrets Manager** - Secure storage for GitHub tokens and webhook secrets
- **IAM Roles** - Service roles for EC2 and Fargate runners

### Monitoring & Logging

- **API Gateway Access Logs** - One month retention in CloudWatch
- **Lambda Function Logs** - One week retention for execution logs
- **Container Insights** - ECS cluster monitoring enabled

## Prerequisites

Before deploying this infrastructure, ensure you have:

1. **AWS CLI** configured with appropriate permissions
2. **AWS CDK** installed and bootstrapped in your target region
3. **Parent Domain** hosted zone already exists in Route53
4. **GitHub Token** stored in AWS Secrets Manager
5. **Python 3.11+** for local development

### Required AWS Permissions

Your deployment role needs permissions for:

- API Gateway (create/modify REST APIs)
- Lambda (create/update functions)
- Route53 (create DNS records)
- ACM (request/validate certificates)
- CloudWatch Logs (create log groups)
- ECS/Fargate (create clusters and task definitions)
- ECR (create repositories)
- Secrets Manager (create/read secrets)
- IAM (create roles and policies)

## API Endpoints

### Health Check Endpoint

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "service": "10U Labs API",
  "version": "1.0.0"
}
```

### Echo Endpoint

```http
POST /v1/echo
Content-Type: application/json

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

### Error Handling

All endpoints return appropriate HTTP status codes:

- **200** - Success
- **400** - Bad Request (invalid JSON)
- **404** - Not Found (undefined endpoints)

## Configuration

The stack expects a configuration dictionary with the following structure:

```python
config = {
    "domain_names": {
        "parent": "example.com",
        "subdomain": "api.example.com"
    },
    "naming": {
        "vpc_name": "10ulabs-vpc",
        "cluster_name": "github-runners",
        "github_token_secret_name": "github-token"
    },
    "aws": {
        "vpc": {
            "cidr": "10.0.0.0/16",
            "max_azs": 2,
            "nat_gateways": 1
        }
    }
}
```

## Deployment Instructions

### 1. Install Dependencies

```bash
pip install aws-cdk-lib constructs
```

### 2. Set Up Configuration

Create your configuration file with appropriate domain names and settings.

### 3. Deploy the Stack

```bash
cdk deploy ApiStack
```

### 4. Verify Deployment

After deployment completes, test the health endpoint:

```bash
curl https://your-subdomain.example.com/health
```

## Testing the API

### Using curl

Test the health endpoint:

```bash
curl -X GET https://your-api-domain.com/health
```

Test the echo endpoint:

```bash
curl -X POST https://your-api-domain.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

### Using Python

```python
import requests
import json

# Health check
response = requests.get('https://your-api-domain.com/health')
print(response.json())

# Echo test
data = {"message": "Hello from Python"}
response = requests.post(
    'https://your-api-domain.com/v1/echo',
    json=data
)
print(response.json())
```

## Architecture Notes

### Serverless Design

The API uses a serverless architecture with the following benefits:

- **No server management** - AWS handles all underlying infrastructure
- **Automatic scaling** - Scales from zero to handle any load
- **Pay-per-request** - Only pay for actual API calls
- **High availability** - Built-in redundancy and failover

### Security Features

- **SSL/TLS Encryption** - All traffic encrypted in transit
- **IAM Integration** - Fine-grained access control capabilities
- **VPC Isolation** - Runner infrastructure isolated in private network
- **Secrets Management** - Sensitive data stored securely

### Monitoring & Observability

- **CloudWatch Integration** - Automatic metrics and logging
- **Access Logs** - Complete request/response audit trail
- **Custom Metrics** - API Gateway and Lambda metrics available
- **Alerting Ready** - Easy to set up CloudWatch alarms

## Stack Outputs

The stack exports several values for use by other stacks:

- **API URL** - Direct API Gateway URL
- **Custom Domain** - Your custom domain name
- **VPC ID** - For runner infrastructure integration
- **ECS Cluster ARN** - For GitHub runner deployment
- **Security Group IDs** - For network access configuration

These outputs enable modular deployment and integration with other
infrastructure components.
