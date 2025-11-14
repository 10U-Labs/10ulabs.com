# 10U Labs API Infrastructure

A comprehensive AWS CDK infrastructure stack that creates a serverless REST API with Lambda backend, along with supporting infrastructure for GitHub self-hosted runners. This stack deploys a production-ready API Gateway with custom domain, SSL certificate, and comprehensive logging.

## Overview

This infrastructure creates a complete serverless API platform with integrated CI/CD runner capabilities. The API serves as the foundation for 10U Labs services while providing the necessary infrastructure to support GitHub Actions self-hosted runners on both Fargate and EC2.

## Key Features

- **Serverless REST API** with AWS Lambda backend
- **Custom domain** with SSL/TLS certificate
- **CORS enabled** for cross-origin requests
- **Comprehensive logging** with CloudWatch integration
- **GitHub Actions integration** with self-hosted runner support
- **Container orchestration** with ECS Fargate
- **Secure secrets management** with AWS Secrets Manager
- **Network isolation** with dedicated VPC

## Resources Created

### API Infrastructure
- **API Gateway REST API** - Main API endpoint with custom domain support
- **Lambda Function** - Python 3.11 runtime handling API requests
- **ACM Certificate** - SSL/TLS certificate for secure HTTPS connections
- **Route53 A Record** - DNS alias pointing to the API Gateway
- **CloudWatch Log Groups** - Access logs and Lambda execution logs

### Network & Security
- **VPC** - Dedicated virtual private cloud with public subnets
- **Security Groups** - Network access controls for runners
- **IAM Roles** - Service roles for EC2 and Fargate runners
- **Secrets Manager** - Secure storage for GitHub tokens and webhook secrets

### Container Infrastructure
- **ECR Repository** - Docker image registry for runner containers
- **ECS Cluster** - Container orchestration platform
- **Fargate Task Definition** - Serverless container configuration
- **Instance Profile** - EC2 permissions for self-hosted runners

## Prerequisites

- AWS CDK v2.x installed and configured
- Python 3.11 or later
- AWS CLI configured with appropriate permissions
- Existing Route53 hosted zone for parent domain
- GitHub token stored in AWS Secrets Manager

### Required AWS Permissions
- API Gateway management
- Lambda function deployment
- Certificate Manager operations
- Route53 DNS management
- VPC and networking resources
- ECS and ECR operations
- IAM role creation
- Secrets Manager access

## API Endpoints

### Health Check
```
GET /health
```
Returns API health status and version information.

**Response:**
```json
{
  "status": "healthy",
  "service": "10U Labs API",
  "version": "1.0.0"
}
```

### Echo Service
```
POST /v1/echo
```
Echoes back the request body with additional metadata.

**Request Body:** Any valid JSON
**Response:**
```json
{
  "echo": { /* your request body */ },
  "received_at": "request-id"
}
```

### Error Handling
- **400 Bad Request** - Invalid JSON in request body
- **404 Not Found** - Endpoint not found
- All responses include CORS headers

## Configuration

The stack requires a configuration object with the following structure:

```python
config = {
    "domain_names": {
        "parent": "example.com",
        "subdomain": "api.example.com"
    },
    "naming": {
        "vpc_name": "runner-vpc",
        "cluster_name": "runner-cluster",
        "github_token_secret_name": "github-token",
        "webhook_secret_name": "webhook-secret"
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

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your settings**
   - Update the configuration object with your domain names
   - Ensure GitHub token is stored in Secrets Manager
   - Verify Route53 hosted zone exists

4. **Deploy the stack**
   ```bash
   cdk deploy
   ```

5. **Verify deployment**
   - Check CloudFormation console for stack status
   - Test API endpoints using the custom domain
   - Verify SSL certificate is properly configured

## Testing the API

### Using curl
```bash
# Health check
curl https://api.yourdomain.com/health

# Echo test
curl -X POST https://api.yourdomain.com/v1/echo \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, World!"}'
```

### Using Python
```python
import requests

# Health check
response = requests.get('https://api.yourdomain.com/health')
print(response.json())

# Echo test
response = requests.post('https://api.yourdomain.com/v1/echo', 
                        json={"test": "data"})
print(response.json())
```

## Architecture Notes

### Serverless Design
- **Lambda-based backend** ensures automatic scaling and cost optimization
- **API Gateway integration** provides managed API endpoint with caching capabilities
- **CloudWatch logging** enables comprehensive monitoring and debugging

### Security Features
- **SSL/TLS termination** at API Gateway with ACM-managed certificates
- **CORS configuration** allows controlled cross-origin access
- **IAM roles** follow least-privilege principle
- **VPC isolation** for runner infrastructure

### Monitoring & Logging
- **Access logs** capture all API requests with CLF format
- **Lambda logs** retained for 1 week for debugging
- **API Gateway logs** provide detailed request/response information
- **Container insights** enabled for ECS cluster monitoring

### Scalability
- **Auto-scaling Lambda** handles variable API load
- **Fargate runners** provide on-demand compute capacity
- **ECR lifecycle policies** manage container image storage costs
- **Route53 alias records** provide high availability DNS resolution

## Stack Outputs

The deployment creates numerous CloudFormation outputs for integration with other services:
- API Gateway URLs and resource IDs
- VPC and subnet information
- ECR repository details
- ECS cluster configuration
- IAM role ARNs
- Secrets Manager references

These outputs enable easy integration with additional infrastructure components and CI/CD pipelines.