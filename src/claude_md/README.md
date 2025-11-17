# CLAUDE.md Formatter

A Python tool that uses AWS Bedrock to format Markdown documents for
compliance with markdownlint rules. This tool specifically targets
CLAUDE.md files and leverages Claude models through AWS Bedrock for
intelligent formatting corrections.

## Purpose and Key Features

- **Automated Markdown Formatting**: Uses AI to intelligently format
  Markdown content for markdownlint compliance
- **AWS Bedrock Integration**: Leverages Claude models through AWS
  Bedrock for natural language processing
- **Robust Error Handling**: Implements retry logic with exponential
  backoff for API throttling
- **Extended Reasoning**: Supports Claude's extended thinking capability
  for complex formatting decisions
- **Configurable Parameters**: Flexible token limits and model selection

## Main Components

### format_claude_md.py

The core Python script that:

- Reads existing CLAUDE.md content
- Sends formatting requests to AWS Bedrock using Claude models
- Implements retry logic for handling API throttling
- Supports extended reasoning tokens for complex formatting tasks
- Writes the formatted content back to CLAUDE.md

### config.json

Configuration file containing:

- AWS account and region settings
- Bedrock model configuration
- Token limits for generation and reasoning

## Prerequisites and Requirements

### Python Dependencies

This project requires Python 3.6+ and the following packages:

```bash
pip install boto3 botocore
```

### AWS Requirements

- AWS account with Bedrock access
- Appropriate IAM permissions for Bedrock runtime operations
- Access to Claude models in AWS Bedrock

### System Dependencies

- Python 3.6 or higher

## Configuration

### config.json Structure

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

#### Configuration Parameters

- `account_id`: AWS account ID
- `region`: AWS region for Bedrock operations
- `bedrock.max_tokens`: Maximum tokens for content generation
- `bedrock.max_tokens_reasoning`: Maximum tokens for extended thinking
- `bedrock.model_id`: Specific Claude model identifier

## Usage Instructions

### Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install Python dependencies:

   ```bash
   pip install boto3 botocore
   ```

3. Configure AWS credentials (using AWS credentials file, environment
   variables, or IAM roles)

4. Update `config.json` with your AWS account details

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

#### Required Arguments

- `--aws-region`: AWS region for Bedrock service
- `--bedrock-model-id`: Claude model identifier
- `--max-tokens-generation`: Token limit for content generation
- `--max-tokens-reasoning`: Token limit for extended thinking
- `--prompt-file`: Path to prompt template file

### Prerequisites for Execution

1. Ensure `CLAUDE.md` exists in the current directory
2. Create a prompt template file with formatting instructions
3. Verify AWS credentials are properly configured

## Architecture Overview

### Component Interaction Flow

```
CLAUDE.md → format_claude_md.py → AWS Bedrock → Claude Model
    ↑                                                    ↓
    └─────────── Formatted Content ←←←←←←←←←←←←←←←←←←←←←←←┘
```

### Authentication Flow

1. Script uses boto3 to authenticate with AWS
2. AWS credentials obtained from:
   - Environment variables
   - AWS credentials file
   - IAM instance profile
   - IAM roles

### Processing Flow

1. **Input Reading**: Script reads current CLAUDE.md content
2. **Prompt Generation**: Combines content with formatting template
3. **API Call**: Sends request to Bedrock with retry logic
4. **Response Processing**: Extracts formatted text from response
5. **Output Writing**: Saves formatted content back to CLAUDE.md

### Retry Mechanism

- Initial random jitter (5-30 seconds) to prevent thundering herd
- Exponential backoff for throttling exceptions
- Maximum 5 retry attempts
- Random jitter added to backoff intervals

## Security Considerations

### AWS Permissions

Ensure IAM permissions include:

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
      "Resource": "arn:aws:bedrock:*:*:model/*"
    }
  ]
}
```

### Data Privacy

- Content is sent to AWS Bedrock for processing
- Ensure compliance with data governance policies
- Consider data residency requirements when selecting regions

### Credential Management

- Never commit AWS credentials to version control
- Use IAM roles when running on AWS infrastructure
- Implement least-privilege access principles

## Troubleshooting

### Common Issues

#### "CLAUDE.md not found"

Ensure the target file exists in the current working directory:

```bash
ls -la CLAUDE.md
```

#### Bedrock Throttling

If experiencing frequent throttling:

- Increase initial jitter range
- Implement longer backoff intervals
- Consider using different regions or models

#### Authentication Errors

Verify AWS credentials:

```bash
aws sts get-caller-identity
```

#### Model Access Issues

Ensure the specified Claude model is available in your region and
account has access permissions.

### Debug Logging

The script outputs detailed logging to stderr, including:

- Retry attempts and wait times
- Token usage and reasoning configuration
- Response structure analysis
- Content block identification

### Performance Optimization

- Adjust `max_tokens` based on content size
- Use appropriate reasoning tokens for complexity
- Consider regional latency when selecting AWS regions
