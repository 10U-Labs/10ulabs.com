# AWS Bedrock Configuration Project

## Overview

This project provides configuration management for AWS Bedrock AI services,
specifically tailored for Claude Sonnet model integration. It centralizes
AWS account settings, regional configurations, and Bedrock-specific parameters
to enable consistent AI model deployment and usage across environments.

## Purpose and Key Features

- **Centralized Configuration**: Single source of truth for AWS Bedrock settings
- **Claude Sonnet Integration**: Pre-configured for Claude Sonnet 4 model
- **Token Management**: Configurable token limits for reasoning and generation
- **Regional Deployment**: US East 1 region configuration
- **Environment Consistency**: Standardized settings across deployments

## Main Components

### Configuration Management

- **config.json**: Core configuration file containing AWS account details,
  regional settings, and Bedrock model parameters
- **AWS Bedrock Integration**: Configuration for Claude Sonnet model with
  customizable token limits for different AI operations

### Key Configuration Elements

- AWS Account ID and region specification
- Bedrock model identification and versioning
- Token allocation for reasoning vs generation tasks
- Model-specific parameter management

## Prerequisites and Requirements

### System Dependencies

- **Node.js**: Required for AWS CDK operations (if using CDK)
- **Git**: For version control and repository management
- **Python 3.7+**: For potential Python-based integrations

### AWS Requirements

- Valid AWS account with Bedrock service access
- Appropriate IAM permissions for Bedrock operations
- Model access permissions for Claude Sonnet in target region

## Configuration Details

### AWS Configuration

The project uses the following AWS configuration structure:

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1",
    "bedrock": {
      "max_tokens_reasoning": 4000,
      "max_tokens_generation": 16000,
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    }
  }
}
```

### Bedrock Model Settings

- **Model ID**: Claude Sonnet 4 (May 2025 version)
- **Reasoning Tokens**: 4,000 token limit for analytical operations
- **Generation Tokens**: 16,000 token limit for content generation
- **Region**: US East 1 (us-east-1)

## Usage Instructions

### Installation Steps

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```

2. Verify configuration file exists:

   ```bash
   ls config.json
   ```

### Configuration Setup

1. Review the current configuration:

   ```bash
   cat config.json
   ```

2. Update configuration values as needed:
   - Modify `account_id` to match your AWS account
   - Adjust token limits based on your use case requirements
   - Change region if deploying to a different AWS region

3. Validate configuration format:

   ```bash
   python -m json.tool config.json
   ```

### Using the Configuration

The configuration can be loaded and used in various ways:

**Python Example:**

```python
import json

with open('config.json', 'r') as f:
    config = json.load(f)

aws_config = config['aws']
bedrock_config = aws_config['bedrock']
```

**Node.js Example:**

```javascript
const config = require('./config.json');
const bedrockConfig = config.aws.bedrock;
```

## Architecture Overview

### Configuration Flow

1. **Central Configuration**: config.json serves as the single source of truth
2. **Application Loading**: Applications load configuration at startup
3. **Service Integration**: Configuration parameters are passed to AWS Bedrock
4. **Model Invocation**: Claude Sonnet model is invoked with specified limits

### Component Interactions

- Configuration file provides parameters to application layer
- Application layer authenticates with AWS using account credentials
- Bedrock service receives model ID and token limits
- Claude Sonnet processes requests within configured constraints

### Authentication Flow

1. AWS credentials resolved through standard AWS credential chain
2. Account ID validation against configured value
3. Regional endpoint resolution based on configuration
4. Bedrock service authentication and model access verification

## Security Considerations

### Configuration Security

- **Account ID Exposure**: Consider using environment variables for sensitive
  account information in production
- **Access Control**: Implement proper IAM policies for Bedrock access
- **Regional Compliance**: Ensure data residency requirements are met with
  chosen region

### Best Practices

- Store sensitive configuration in AWS Systems Manager Parameter Store
- Use IAM roles instead of access keys where possible
- Implement least privilege access for Bedrock operations
- Monitor and log all Bedrock API calls for audit purposes

### Recommendations

- Rotate AWS credentials regularly
- Use AWS CloudTrail for comprehensive API logging
- Implement request rate limiting to prevent quota exhaustion
- Set up billing alerts for Bedrock usage monitoring

## Troubleshooting Tips

### Common Configuration Issues

**Invalid JSON Format:**

```bash
# Validate JSON syntax
python -m json.tool config.json
```

**Account ID Mismatch:**

- Verify the account ID matches your AWS account
- Check AWS CLI configuration: `aws sts get-caller-identity`

**Region Access Issues:**

- Confirm Bedrock is available in the configured region
- Verify Claude Sonnet model access in the target region

### Model Access Problems

1. **Check Model Availability:**
   - Verify model ID is correct for your region
   - Confirm model access has been requested and approved

2. **Token Limit Errors:**
   - Review and adjust max_tokens_reasoning and max_tokens_generation
   - Monitor actual usage against configured limits

3. **Authentication Failures:**
   - Verify AWS credentials are properly configured
   - Check IAM permissions for Bedrock service access

### Performance Optimization

- Adjust token limits based on actual usage patterns
- Monitor response times and adjust regional configuration if needed
- Implement caching strategies for repeated model invocations
- Consider using multiple regions for improved latency
