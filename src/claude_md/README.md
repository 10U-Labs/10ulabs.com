# Claude Markdown Formatter

A Python utility that leverages AWS Bedrock to automatically format Markdown
files to comply with markdownlint rules using Claude AI models.

## Overview

This project provides an automated solution for formatting Markdown content
using AWS Bedrock's Claude AI models. It reads existing Markdown files,
processes them through Claude to ensure compliance with markdownlint rules,
and writes the formatted content back to the file system.

## Key Features

- **AI-Powered Formatting**: Uses Claude AI models via AWS Bedrock for
  intelligent Markdown formatting
- **Retry Logic**: Implements exponential backoff with jitter for handling
  API throttling
- **Extended Reasoning**: Supports Claude's extended thinking capabilities
  for complex formatting decisions
- **Configurable Parameters**: Flexible configuration for token limits,
  model selection, and AWS regions
- **Robust Error Handling**: Comprehensive logging and error recovery

## Components

### Core Module (`format_claude_md.py`)

The main Python script that handles:

- **Bedrock Integration**: Manages AWS Bedrock API calls with retry logic
- **Content Processing**: Reads, processes, and writes Markdown files
- **Configuration Management**: Handles model parameters and AWS settings
- **Error Recovery**: Implements throttling protection and error handling

### Configuration (`config.json`)

Centralized configuration file containing:

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

## Prerequisites

### Python Dependencies

Based on the code analysis, the following Python packages are required:

- `boto3` - AWS SDK for Python (Bedrock API access)
- `botocore` - Core functionality for AWS SDK

### System Requirements

- Python 3.7 or higher
- AWS credentials configured (via IAM roles, profiles, or environment
  variables)
- Access to AWS Bedrock service in your AWS account
- Appropriate IAM permissions for Bedrock model access

## Configuration

### AWS Bedrock Setup

1. Ensure your AWS account has access to Claude models in Bedrock
2. Configure appropriate IAM permissions:

   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock:InvokeModel",
           "bedrock:InvokeModelWithResponseStream"
         ],
         "Resource": "arn:aws:bedrock:*:*:foundation-model/anthropic.claude*"
       }
     ]
   }
   ```

### Model Configuration

Edit `config.json` to customize:

- `account_id`: Your AWS account ID
- `region`: AWS region where Bedrock is available
- `max_tokens`: Maximum tokens for content generation
- `max_tokens_reasoning`: Tokens allocated for extended thinking
- `model_id`: Specific Claude model version to use

## Usage

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd claude-markdown-formatter
   ```

2. Install Python dependencies:

   ```bash
   pip install boto3 botocore
   ```

3. Configure AWS credentials using one of these methods:

   ```bash
   # Using AWS credentials file
   aws configure
   
   # Or set environment variables
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
  --prompt-file prompt_template.txt
```

### Required Files

- `CLAUDE.md`: The Markdown file to be formatted (must exist)
- Prompt template file: Contains formatting instructions for Claude

## Architecture

### Data Flow

1. **Input Processing**: Script reads existing `CLAUDE.md` file
2. **Template Loading**: Loads prompt template with formatting instructions
3. **Bedrock Request**: Sends content and prompt to Claude via AWS Bedrock
4. **Response Processing**: Extracts formatted content from API response
5. **Output Generation**: Writes formatted content back to `CLAUDE.md`

### Authentication Flow

- Uses boto3 SDK for AWS authentication
- Supports multiple credential sources (IAM roles, profiles, environment
  variables)
- Automatically handles credential refresh and token management

### Retry Mechanism

- Implements exponential backoff for throttling errors
- Uses random jitter to prevent thundering herd problems
- Configurable retry attempts (default: 5 attempts)

## Security Considerations

### Access Control

- Use IAM roles with minimal required permissions
- Restrict Bedrock access to specific model ARNs
- Consider using AWS STS for temporary credentials

### Data Privacy

- Markdown content is sent to AWS Bedrock for processing
- Ensure compliance with data residency requirements
- Review AWS Bedrock data handling policies

### Network Security

- All API calls use HTTPS encryption
- Consider using VPC endpoints for enhanced security
- Implement network-level access controls as needed

## Troubleshooting

### Common Issues

**Bedrock Throttling**:

- Increase initial jitter delay
- Reduce concurrent requests
- Check service quotas in AWS console

**Authentication Errors**:

- Verify AWS credentials are properly configured
- Check IAM permissions for Bedrock access
- Ensure correct AWS region is specified

**Model Access Denied**:

- Verify model availability in your AWS region
- Check if Claude models are enabled in Bedrock console
- Confirm model ID format matches AWS specifications

**File Not Found**:

- Ensure `CLAUDE.md` exists in working directory
- Verify prompt template file path is correct
- Check file permissions for read/write access

### Debugging

Enable detailed logging by modifying the logging level:

```python
logging.basicConfig(level=logging.DEBUG)
```

Monitor AWS CloudTrail for Bedrock API call details and error analysis.
