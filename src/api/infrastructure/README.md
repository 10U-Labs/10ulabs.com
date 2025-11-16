# 10U Labs API Infrastructure

A comprehensive AWS CDK infrastructure stack for deploying the 10U Labs API
service at `api.10ulabs.com`. This infrastructure provides a scalable API
Gateway with Lambda functions, CloudFront distribution, and supporting
GitHub Actions self-hosted runner infrastructure.

## Purpose and Key Features

This infrastructure creates a production-ready API service with:

- REST API Gateway with custom domain and SSL certificate
- Lambda functions for health checks, echo endpoints, and catch-all routing
- CloudFront distribution for global content delivery
- S3 bucket hosting for API documentation
- GitHub Actions self-hosted runners on both ECS Fargate and EC2
- VPC with public subnets for runner infrastructure
- ECR repository for containerized runner images
- Comprehensive security groups and IAM roles
- Web Application Firewall (WAF) protection

## Resources Created

### Core API Infrastructure

- **API Gateway REST API** (`TenULabsApi`): Main API service with OpenAPI
  specification
- **Lambda Functions**: Health check, echo endpoint, and catch-all handlers
- **CloudFront Distribution**: Global CDN with custom behaviors for API and
  documentation
- **Route 53 Records**: DNS alias records pointing to CloudFront
- **ACM Certificate**: SSL/TLS certificate for `api.10ulabs.com`
- **S3 Bucket**: Static hosting for OpenAPI documentation and landing pages

### GitHub Actions Runner Infrastructure

- **VPC**: Dedicated network (10.0.0.0/16) for runner instances
- **ECS Cluster**: Fargate-based GitHub Actions runners
- **ECR Repository**: Container registry for runner Docker images
- **ECS Task Definition**: Fargate task configuration with GitHub token
  integration
- **EC2 IAM Role**: Instance profile for EC2-based runners with ECR access
- **Security Groups**: Network access controls for runner instances

### Security and Configuration

- **WAF Web ACL**: CloudFront protection against common web exploits
- **Secrets Manager**: GitHub token and webhook secret storage
- **IAM Roles**: Least-privilege access for all components
- **CloudWatch Logs**: Centralized logging for API Gateway and Lambda
  functions

## Prerequisites and Requirements

### Python Dependencies

Install the required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

Required packages:

- `aws-cdk-lib==2.150.0`: AWS CDK framework
- `constructs>=10.0.0,<11.0.0`: CDK constructs library
- `boto3>=1.34.0`: AWS SDK for Python
- `boto3-stubs[route53,route53domains,account,organizations]>=1.34.0`:
  Type hints for boto3
- `requests>=2.31.0`: HTTP library for API calls
- `types-requests>=2.31.0`: Type hints for requests
- `pyyaml>=6.0.1`: YAML parsing for OpenAPI specification
- `types-pyyaml>=6.0.12`: Type hints for PyYAML

### System Dependencies

- **Python 3.11+**: Runtime environment for CDK application
- **Node.js 18+**: Required by AWS CDK framework
- **Git**: Version control for source code management

### AWS Prerequisites

- AWS account with appropriate permissions for CDK deployment
- Existing Route 53 hosted zone for `10ulabs.com`
- GitHub token stored in AWS Secrets Manager at
  `github-runner/credentials`

## Configuration

### Primary Configuration (`config.json`)

The infrastructure is configured through `config.json`:

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1",
    "bedrock": {
      "max_tokens_reasoning": 4000,
      "max_tokens_generation": 16000,
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    },
    "vpc": {
      "cidr": "10.0.0.0/16",
      "max_azs": 99,
      "nat_gateways": 0,
      "subnet_configuration": {
        "public_subnet_cidr_mask": 24
      }
    }
  },
  "domain_names": {
    "parent": "10ulabs.com",
    "subdomain": "api.10ulabs.com"
  }
}
```

### CDK Configuration (`cdk.json`)

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

## Usage Instructions

### Installation

1. Clone the repository and navigate to the infrastructure directory:

   ```bash
   git clone <repository-url>
   cd infrastructure
   ```

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Install Node.js dependencies for CDK:

   ```bash
   npm install -g aws-cdk
   ```

### Deployment

1. Configure AWS credentials:

   ```bash
   # Using AWS profile
   export AWS_PROFILE=your-profile-name
   
   # Or using environment variables
   export AWS_ACCESS_KEY_ID=your-access-key
   export AWS_SECRET_ACCESS_KEY=your-secret-key
   ```

2. Bootstrap CDK (first time only):

   ```bash
   cdk bootstrap
   ```

3. Deploy the infrastructure:

   ```bash
   cdk deploy TenULabsApi
   ```

### Using the Deployed Resources

#### API Endpoints

- **Health Check**: `GET https://api.10ulabs.com/health`
- **Echo Service**: `POST https://api.10ulabs.com/v1/echo`
- **API Documentation**: `https://api.10ulabs.com/`
- **OpenAPI Specification**: `https://api.10ulabs.com/openapi.yaml`

#### GitHub Actions Runners

The infrastructure automatically provisions self-hosted runners:

- **Fargate Runners**: Ephemeral containers with label
  `ephemeral-ecs-fargate-spot`
- **EC2 Runners**: Spot instances with label `ephemeral-ec2-spot-instance`

### Maintenance Scripts

Generate or update documentation using the included script:

```bash
python3 scripts/readme.py --update --project-dir . \
  --aws-region us-east-1 --output-file /tmp/result \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-reasoning 4000 --max-tokens-generation 16000
```

## Architecture Overview

### Request Flow

1. **DNS Resolution**: Route 53 resolves `api.10ulabs.com` to CloudFront
2. **CloudFront Distribution**: Routes requests based on path patterns:
   - `/` → S3 bucket (documentation)
   - `/health` → API Gateway → Health Lambda
   - `/v1/*` → API Gateway → Respective Lambda functions
   - `/openapi.yaml` → S3 bucket
3. **API Gateway**: Validates requests and routes to appropriate Lambda
   functions
4. **Lambda Functions**: Process requests and return responses

### GitHub Actions Integration

1. **Webhook Reception**: GitHub sends webhook events to API Gateway
2. **Runner Provisioning**: ECS tasks or EC2 instances are launched based
   on workload requirements
3. **Job Execution**: Self-hosted runners pull jobs from GitHub and
   execute workflows
4. **Resource Cleanup**: Ephemeral runners terminate after job completion

### Authentication and Authorization

- **API Gateway**: No authentication required for public endpoints
- **GitHub Runners**: Authenticate using GitHub token from Secrets Manager
- **AWS Resources**: IAM roles provide least-privilege access
- **Webhook Security**: GitHub webhook signatures verified using shared
  secret

## Security Considerations

### Network Security

- **VPC Isolation**: Runner infrastructure operates in dedicated VPC
- **Security Groups**: Restrictive ingress rules, allow all egress for
  GitHub connectivity
- **Public Subnets**: No NAT gateways to reduce costs, runners use public
  IPs

### Access Control

- **IAM Roles**: Separate roles for Lambda functions, ECS tasks, and EC2
  instances
- **Secrets Management**: GitHub tokens stored in AWS Secrets Manager
- **ECR Access**: Runners can pull container images but not push

### Web Security

- **WAF Protection**: CloudFront distribution protected by Web Application
  Firewall
- **SSL/TLS**: All traffic encrypted using ACM certificates
- **HTTPS Redirect**: HTTP requests automatically redirected to HTTPS

### Resource Protection

- **Spot Instances**: EC2 runners use spot instances with maximum price
  limits
- **Lifecycle Management**: ECR images limited to 3 most recent versions
- **Log Retention**: CloudWatch logs retained for 1 week (Lambda) to 1
  month (API Gateway)

## Troubleshooting

### Common Issues

#### CDK Deployment Failures

- **Bootstrap Required**: Run `cdk bootstrap` if encountering asset upload
  errors
- **Permissions**: Ensure AWS credentials have sufficient permissions for
  all resource types
- **Certificate Validation**: DNS validation may take several minutes for
  ACM certificates

#### API Gateway Issues

- **OpenAPI Validation**: Check `openapi.yaml` syntax if deployment fails
- **Lambda Permissions**: Verify API Gateway has invoke permissions for
  all Lambda functions
- **CORS Headers**: Add appropriate CORS headers if experiencing
  cross-origin issues

#### GitHub Runner Problems

- **Token Expiration**: Rotate GitHub token in Secrets Manager if runners
  fail to register
- **ECR Authentication**: Ensure EC2 instance profile has ECR permissions
- **Network Connectivity**: Check security group rules if runners cannot
  reach GitHub

### Debugging Commands

Check stack outputs:

```bash
aws cloudformation describe-stacks --stack-name TenULabsApi \
  --query 'Stacks[0].Outputs'
```

View Lambda logs:

```bash
aws logs describe-log-groups --log-group-name-prefix /aws/lambda/
```

Test API endpoints:

```bash
curl -v https://api.10ulabs.com/health
curl -X POST https://api.10ulabs.com/v1/echo -d '{"test": "data"}' \
  -H "Content-Type: application/json"
```

### Performance Monitoring

- **CloudWatch Metrics**: Monitor API Gateway request counts and latencies
- **Lambda Insights**: Track function duration and memory usage
- **CloudFront Analytics**: Monitor global distribution performance
- **ECS Container Insights**: Track runner resource utilization
