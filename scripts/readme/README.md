# AWS Bedrock Infrastructure Configuration

## Overview

This project provides configuration settings for AWS Bedrock, Amazon's managed
service for foundation models. The configuration defines essential parameters
for AI model interactions including token limits, model selection, and regional
deployment settings.

## Purpose and Key Features

- **Model Configuration**: Centralized configuration for AWS Bedrock Claude
  Sonnet model
- **Token Management**: Configurable limits for reasoning and generation tasks
- **Regional Deployment**: US East 1 region configuration for optimal
  performance
- **Account Management**: Structured AWS account targeting

### Key Capabilities

- Support for Claude Sonnet 4 model (latest version as of May 2024)
- Separate token allocation for reasoning (4,000) and generation (16,000)
- Production-ready configuration structure
- Environment-specific settings management

## Resources and Configuration

### AWS Resources Referenced

- **AWS Bedrock**: Foundation model service configuration
- **Claude Sonnet Model**: `us.anthropic.claude-sonnet-4-20250514-v1:0`
- **AWS Account**: Target account `781581267945`
- **AWS Region**: `us-east-1` (US East - N. Virginia)

## Prerequisites and Requirements

### System Dependencies

- **Python 3.8+**: Required for configuration management
- **Git**: For version control and repository management

### AWS Requirements

- AWS account with Bedrock service access
- Appropriate IAM permissions for Bedrock model usage
- Model access granted for Claude Sonnet in the target region

## Configuration Details

The main configuration is stored in `config.json`:

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

### Configuration Parameters

| Parameter | Value | Description |
| --- | --- | --- |
| `account_id` | 781581267945 | Target AWS account identifier |
| `region` | us-east-1 | AWS region for resource deployment |
| `max_tokens_reasoning` | 4000 | Token limit for reasoning operations |
| `max_tokens_generation` | 16000 | Token limit for text generation |
| `model_id` | claude-sonnet-4 | Specific Bedrock model version |

## Usage Instructions

### Installation Steps

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Verify Configuration**

   ```bash
   cat config.json
   ```

3. **Validate AWS Access**

   Ensure your AWS credentials are configured with appropriate permissions
   for Bedrock service access.

### Configuration Usage

1. **Load Configuration in Applications**

   ```python
   import json
   
   with open('config.json', 'r') as f:
       config = json.load(f)
   
   bedrock_config = config['aws']['bedrock']
   model_id = bedrock_config['model_id']
   ```

2. **Environment-Specific Overrides**

   Create environment-specific configuration files:

   ```bash
   cp config.json config.dev.json
   cp config.json config.prod.json
   ```

3. **Integrate with Applications**

   Use the configuration in your Bedrock client applications to ensure
   consistent model parameters and limits across deployments.

## Architecture Overview

### Configuration Flow

1. **Configuration Loading**: Applications load settings from `config.json`
2. **AWS Service Integration**: Settings apply to Bedrock API calls
3. **Model Interaction**: Token limits enforce usage boundaries
4. **Response Handling**: Generation limits prevent excessive resource usage

### Component Interactions

- **Application Layer**: Consumes configuration settings
- **AWS Bedrock Service**: Receives configured parameters
- **Claude Sonnet Model**: Processes requests within token limits
- **Response Management**: Handles output within generation limits

### Authentication Flow

- Applications use AWS SDK credentials (IAM roles, profiles, or keys)
- Bedrock service validates permissions for model access
- Regional configuration ensures proper service endpoint usage

## Security Considerations

### Configuration Security

- **Sensitive Data**: Account ID is visible; consider environment variables
  for production deployments
- **Access Control**: Implement proper IAM policies for Bedrock access
- **Token Limits**: Configured limits prevent excessive usage and costs

### Best Practices

- Store configuration in secure, version-controlled repositories
- Use environment-specific configurations for different deployment stages
- Implement monitoring for token usage and model invocations
- Regular review of model permissions and access patterns

### IAM Requirements

Ensure the following permissions for Bedrock access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:GetModel"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-*"
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **Model Access Denied**

   - Verify Bedrock service is available in your region
   - Check IAM permissions for model access
   - Ensure Claude Sonnet model access is granted in AWS Console

2. **Configuration Loading Errors**

   ```bash
   # Validate JSON syntax
   python -m json.tool config.json
   ```

3. **Token Limit Exceeded**

   - Review and adjust `max_tokens_reasoning` and `max_tokens_generation`
   - Monitor actual usage patterns in your applications
   - Implement proper error handling for token limit responses

4. **Regional Issues**

   - Verify Claude Sonnet availability in `us-east-1`
   - Check for regional service limitations
   - Consider alternative regions if needed

### Debug Steps

1. Validate configuration file syntax and structure
2. Test AWS credentials and permissions
3. Verify Bedrock service availability
4. Check model-specific access and quotas
5. Monitor CloudTrail logs for access patterns and errors

For additional support, consult AWS Bedrock documentation and service status
pages for region-specific availability and limitations.
