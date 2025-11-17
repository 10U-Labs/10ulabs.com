# Claude Markdown Formatter

A Python tool that uses AWS Bedrock to automatically format Markdown files to
comply with markdownlint rules. This tool specifically processes a `CLAUDE.md`
file and reformats it using Claude AI models through the AWS Bedrock service.

## Purpose and Key Features

- **Automated Markdown Formatting**: Leverages AWS Bedrock's Claude models to
  intelligently format Markdown content
- **Markdownlint Compliance**: Ensures output follows strict markdownlint rules
- **Retry Logic**: Built-in exponential backoff and retry mechanism for
  handling API throttling
- **Extended Reasoning**: Supports Claude's extended thinking capabilities for
  better formatting decisions
- **Configurable Parameters**: Customizable token limits and model selection

## Main Components

### format_claude_md.py

The main Python script that handles:

- Reading existing `CLAUDE.md` content
- Interfacing with AWS Bedrock runtime API
- Processing prompt templates for formatting instructions
- Implementing retry logic with exponential backoff
- Writing formatted content back to the file

### config.json

Configuration file containing:

- AWS account ID and region settings
- Bedrock model configuration including token limits
- Model ID specification for Claude Sonnet

## Prerequisites and Requirements

### Python Dependencies

This project requires Python 3.6+ and the following packages:

```text
boto3
botocore
```

### AWS Requirements

- AWS account with Bedrock access enabled
- IAM permissions for `bedrock-runtime:InvokeModel`
- AWS credentials configured (via AWS credentials file, environment variables,
  or IAM roles)

### System Dependencies

- Python 3.6 or higher

## Configuration

The project uses a `config.json` file for AWS and Bedrock settings:

```json
{
  "account_id": 781581267945,
  "region": "us-east-1",
  "bedrock": {
    "max_tokens": 16000,
    "max_tokens_reasoning": 4000,
    "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
  }
}
```

### Configuration Parameters

| Parameter | Description |
| --- | --- |
| `account_id` | AWS account ID |
| `region` | AWS region for Bedrock service |
| `max_tokens` | Maximum tokens for content generation |
| `max_tokens_reasoning` | Token budget for extended thinking |
| `model_id` | Specific Claude model version to use |

## Usage Instructions

### Installation

1. Clone the repository and navigate to the project directory

2. Install Python dependencies:

   ```bash
   pip install boto3 botocore
   ```

3. Configure AWS credentials using one of these methods:

   ```bash
   # Option 1: AWS credentials file
   aws configure
   
   # Option 2: Environment variables
   export AWS_ACCESS_KEY_ID=your_access_key
   export AWS_SECRET_ACCESS_KEY=your_secret_key
   export AWS_DEFAULT_REGION=us-east-1
   ```

### Running the Formatter

Execute the script with required parameters:

```bash
python3 format_claude_md.py \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-generation 16000 \
  --max-tokens-reasoning 4000 \
  --prompt-file prompt.txt
```

### Prerequisites for Execution

1. Ensure `CLAUDE.md` exists in the current directory
2. Create a prompt template file containing formatting instructions
3. Verify AWS Bedrock access is enabled for your account

## Architecture Overview

### Component Interaction Flow

```text
CLAUDE.md → format_claude_md.py → AWS Bedrock → Formatted CLAUDE.md
```

1. **Input Processing**: Script reads existing `CLAUDE.md` content
2. **Prompt Generation**: Combines content with formatting instructions
3. **API Communication**: Sends request to AWS Bedrock with retry logic
4. **Response Processing**: Extracts formatted content from API response
5. **Output Writing**: Overwrites original file with formatted content

### Authentication Flow

- Uses boto3 SDK for AWS authentication
- Supports multiple credential sources (credentials file, environment
  variables, IAM roles)
- Requires `bedrock-runtime:InvokeModel` permissions

### Data Flow

1. Local `CLAUDE.md` file is read into memory
2. Content is embedded in a prompt template
3. Request is sent to Bedrock with exponential backoff retry logic
4. Response content is validated and processed
5. Formatted content replaces the original file

## Security Considerations

### AWS Security

- **IAM Permissions**: Use least-privilege principle, only grant necessary
  Bedrock permissions
- **Credential Management**: Never hardcode AWS credentials in source code
- **Network Security**: Bedrock API calls use HTTPS encryption

### Data Handling

- Content is processed through AWS Bedrock service
- Ensure compliance with data residency requirements
- Consider data sensitivity when using cloud AI services

### Best Practices

- Rotate AWS access keys regularly
- Use IAM roles when running on EC2 instances
- Monitor CloudTrail logs for API usage
- Implement proper error handling to avoid credential leakage

## Troubleshooting

### Common Issues

**ThrottlingException Errors**

```bash
# The script includes automatic retry logic
# Increase initial jitter or retry delays if needed
```

**Missing CLAUDE.md File**

```bash
# Ensure CLAUDE.md exists in the current directory
touch CLAUDE.md  # Create empty file if needed
```

**AWS Authentication Failures**

```bash
# Verify credentials are configured
aws sts get-caller-identity

# Check IAM permissions for Bedrock access
```

**Model Access Issues**

- Verify the specified Claude model is available in your AWS region
- Check if model access has been requested and approved in the AWS console
- Ensure the model ID format matches AWS Bedrock specifications

### Debug Logging

The script provides detailed logging to stderr:

- API call attempts and success/failure status
- Token configuration and reasoning enablement
- Content processing and validation steps

### Performance Optimization

- Initial jitter (5-30 seconds) prevents thundering herd problems
- Exponential backoff reduces API pressure during throttling
- Token limits prevent excessive API costs
