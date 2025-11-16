# 10U Labs API Infrastructure

Comprehensive AWS infrastructure for hosting the 10U Labs API at
`api.10ulabs.com`, providing REST endpoints, documentation hosting,
and GitHub self-hosted runner capabilities using AWS CDK.

## Purpose and Key Features

This infrastructure stack creates a production-ready API platform with:

- **REST API Gateway**: Custom domain with SSL/TLS termination
- **Lambda Functions**: Serverless endpoint handlers for health checks,
  echo testing, and catch-all routing
- **CloudFront Distribution**: Global CDN for API caching and static
  documentation hosting
- **GitHub Self-Hosted Runners**: Both Fargate and EC2-based runners
  for CI/CD workflows
- **S3 Documentation**: Automated deployment of OpenAPI documentation
- **WAF Protection**: Web Application Firewall for security
- **Route 53 Integration**: DNS management with existing hosted zone

## Resources Created

### Core API Infrastructure

- **API Gateway REST API**: Main API endpoint with OpenAPI specification
- **Lambda Functions**:
  - Health check endpoint (`/health`)
  - Echo testing endpoint (`/v1/echo`)
  - Catch-all handler for undefined routes
- **CloudWatch Log Groups**: API access logs and Lambda execution logs

### Content Delivery and Storage

- **CloudFront Distribution**: Multi-origin distribution serving both
  API requests and static documentation
- **S3 Bucket**: Hosts OpenAPI documentation files (`openapi.yaml`,
  `index.html`, `404.html`)
- **CloudFront Functions**: URL rewriting for S3 origin routing

### GitHub Self-Hosted Runners

- **VPC**: Isolated network for runner instances
- **ECS Fargate Cluster**: Container-based ephemeral runners
- **ECR Repository**: Docker image storage for runner containers
- **ECS Task Definition**: Fargate task configuration with GitHub
  token integration
- **EC2 IAM Roles**: Instance profiles for EC2-based runners with
  ECR access and self-termination permissions

### Security and Secrets Management

- **ACM Certificate**: SSL/TLS certificate for custom domain
- **AWS Secrets Manager**: GitHub tokens and webhook secrets
- **WAF Web ACL**: Protection against common web attacks
- **Security Groups**: Network access control for runner instances

### DNS and Monitoring

- **Route 53 A Record**: DNS alias pointing to CloudFront distribution
- **CloudWatch Logs**: Centralized logging with retention policies

## Prerequisites and Requirements

### Python Dependencies

Install the required Python packages from `requirements.txt`:

```bash
pip install -r requirements.txt
```

Required packages:

- `aws-cdk-lib==2.150.0`
- `constructs>=10.0.0,<11.0.0`
- `boto3>=1.34.0`
- `boto3-stubs[route53,route53domains,account,organizations]>=1.34.0`
- `requests>=2.31.0`
- `types-requests>=2.31.0`
- `pyyaml>=6.0.1`
- `types-pyyaml>=6.0.12`

### System Dependencies

- **Node.js**: Required for AWS CDK (version 14.x or later)
- **Python**: Version 3.8 or later
- **Git**: For repository operations

### AWS Prerequisites

- AWS account with appropriate permissions for CDK deployment
- Existing Route 53 hosted zone for parent domain (`10ulabs.com`)
- GitHub organization and repository for self-hosted runners
- Pre-created GitHub token secret in AWS Secrets Manager

## Configuration

### Primary Configuration (`config.json`)

The infrastructure is configured through `config.json`:

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
  },
  "github": {
    "org": "10U-Labs-LLC",
    "repo": "10U-Labs-LLC/10ulabs.com"
  }
}
```

### CDK Configuration (`cdk.json`)

CDK-specific settings and feature flags:

```json
{
  "app": "python3 app.py",
  "watch": {
    "include": ["**"],
    "exclude": ["README.md", "cdk*.json", "**/__pycache__"]
  }
}
```

### Required Secrets

Before deployment, create these secrets in AWS Secrets Manager:

1. **GitHub Token**: `github-runner/credentials` - Personal access
   token with repo and workflow permissions
2. **Webhook Secret**: Auto-generated during deployment for GitHub
   webhook signature verification

## Usage Instructions

### Installation

1. Clone the repository and navigate to the infrastructure directory:

   ```bash
   git clone <repository-url>
   cd infrastructure/
   ```

2. Install Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Install AWS CDK globally:

   ```bash
   npm install -g aws-cdk
   ```

4. Configure AWS credentials (via AWS credentials file, environment
   variables, or IAM roles)

### Deployment

1. Bootstrap CDK in your AWS account (first time only):

   ```bash
   cdk bootstrap
   ```

2. Deploy the infrastructure:

   ```bash
   cdk deploy
   ```

3. Confirm the deployment when prompted

### Using the Deployed Resources

#### API Endpoints

Access the API through the custom domain:

- **Health Check**: `GET https://api.10ulabs.com/health`
- **Echo Endpoint**: `POST https://api.10ulabs.com/v1/echo`
- **Documentation**: `https://api.10ulabs.com/` (serves OpenAPI docs)

#### GitHub Self-Hosted Runners

The infrastructure provides two types of runners:

1. **Fargate Runners**: Ephemeral containers with labels
   `["ephemeral-ecs-fargate-spot"]`
2. **EC2 Runners**: Spot instances with labels
   `["ephemeral-ec2-spot-instance"]`

Configure GitHub Actions workflows to use these runners:

```yaml
jobs:
  example:
    runs-on: [self-hosted, ephemeral-ecs-fargate-spot]
```

#### Documentation Updates

Place documentation files in the project root:

- `openapi.yaml`: OpenAPI specification
- `index.html`: API documentation homepage
- `404.html`: Custom error page

Files are automatically deployed to S3 and served via CloudFront.

### Infrastructure Management

View stack outputs:

```bash
cdk list
cdk diff
```

Destroy the infrastructure:

```bash
cdk destroy
```

## Architecture Overview

### Request Flow

1. **DNS Resolution**: Route 53 resolves `api.10ulabs.com` to
   CloudFront distribution
2. **CloudFront Routing**: Distribution routes requests based on path:
   - `/` → S3 origin (documentation)
   - `/health` → API Gateway origin
   - `/v1/*` → API Gateway origin
   - Other paths → API Gateway catch-all
3. **API Gateway**: Processes API requests and invokes appropriate
   Lambda functions
4. **Lambda Execution**: Functions process requests and return responses

### Runner Architecture

#### Fargate Runners

- **ECS Cluster**: Manages containerized runner tasks
- **Task Definition**: Configures runner containers with GitHub
  integration
- **ECR Repository**: Stores custom runner Docker images
- **Secrets Integration**: Injects GitHub tokens securely

#### EC2 Runners

- **IAM Roles**: Provide necessary permissions for ECR access and
  instance self-termination
- **Instance Profiles**: Attach roles to EC2 instances
- **Security Groups**: Control network access

### Security Architecture

- **WAF**: Filters malicious requests before they reach origins
- **CloudFront**: Provides DDoS protection and SSL termination
- **VPC Isolation**: Runners execute in private network segments
- **Secrets Manager**: Secure storage and rotation of sensitive data
- **IAM Least Privilege**: Minimal permissions for all components

## Security Considerations

### Network Security

- **VPC Isolation**: All runner infrastructure operates within a
  dedicated VPC
- **Public Subnets Only**: Cost-optimized configuration without NAT
  gateways for outbound internet access
- **Security Groups**: Restrictive ingress rules, permissive egress
  for GitHub API communication

### Access Control

- **IAM Roles**: Separate roles for different components with minimal
  required permissions
- **Cross-Service Permissions**: API Gateway can invoke Lambda
  functions; ECS can pull from ECR
- **Self-Termination**: EC2 runners can only terminate instances with
  specific tags

### Secrets Management

- **GitHub Tokens**: Stored in AWS Secrets Manager with automatic
  rotation capabilities
- **Webhook Signatures**: Auto-generated secrets for GitHub webhook
  verification
- **Container Environment**: Secrets injected securely into ECS tasks

### SSL/TLS

- **End-to-End Encryption**: HTTPS enforcement from clients to backend
  services
- **Certificate Management**: Automated certificate provisioning and
  renewal via ACM
- **HSTS**: HTTP Strict Transport Security headers via CloudFront

## Troubleshooting

### Common Issues

#### Certificate Validation Failures

If certificate validation fails during deployment:

1. Verify the parent hosted zone exists and is accessible
2. Check that the domain name configuration matches the actual domain
3. Ensure Route 53 has proper permissions to create validation records

#### API Gateway 403 Errors

For permission denied errors:

1. Check Lambda function permissions for API Gateway invocation
2. Verify the OpenAPI specification ARN placeholders are correctly
   replaced
3. Review CloudWatch logs for detailed error messages

#### Runner Connection Issues

If GitHub runners fail to connect:

1. Verify GitHub token permissions include `repo` and `workflow` scopes
2. Check ECS task logs for authentication errors
3. Ensure security groups allow outbound HTTPS traffic
4. Confirm ECR repository contains the runner image

#### CloudFront Distribution Issues

For content delivery problems:

1. Check S3 bucket permissions and object existence
2. Verify CloudFront origin configurations
3. Create manual invalidations for cached content updates
4. Review CloudFront access logs for request patterns

### Debugging Commands

Check CDK stack status:

```bash
cdk list --long
```

View detailed differences before deployment:

```bash
cdk diff
```

Access CloudWatch logs:

```bash
aws logs describe-log-groups --log-group-name-prefix="/aws/lambda/"
```

Validate ECR repository contents:

```bash
aws ecr list-images --repository-name github-runner
```

### Log Locations

- **API Gateway Access Logs**: CloudWatch Logs group created by CDK
- **Lambda Function Logs**: `/aws/lambda/<function-name>`
- **ECS Task Logs**: `/aws/ecs/<cluster-name>`
- **CloudFront Access Logs**: Optional S3 bucket (not configured)
