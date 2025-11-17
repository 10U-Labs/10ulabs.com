# Transform to Compliant Markdown

A tool that uses AWS Bedrock's Claude AI to automatically fix markdownlint violations in `CLAUDE.md` files while preserving all original content exactly.

## Overview

This project provides a Python script that leverages AWS Bedrock's Claude Sonnet model to transform markdown files to comply with markdownlint rules. The tool reads an existing `CLAUDE.md` file, processes it through Claude AI with specific formatting instructions, and outputs a compliant version that fixes all markdownlint violations without removing or modifying any content.

## Features

- **Automatic Markdownlint Compliance**: Fixes all common markdownlint violations (MD041, MD013, MD022, MD012, MD009, MD047)
- **Content Preservation**: Maintains all original content exactly - no removal, rephrasing, or summarization
- **AWS Bedrock Integration**: Uses Claude Sonnet 4 model with extended reasoning capabilities
- **Retry Logic**: Built-in exponential backoff and retry handling for AWS API throttling
- **Configurable Parameters**: Supports custom token limits for generation and reasoning

## Requirements

- Python 3.7+
- AWS credentials configured (via IAM roles, environment variables, or AWS CLI)
- Access to AWS Bedrock Claude models in your AWS account
- Required Python packages: `boto3`, `botocore`

## Installation

1. Clone this repository
2. Install required dependencies:
   ```bash
   pip install boto3 botocore
   ```
3. Ensure AWS credentials are properly configured

## Usage

### Basic Usage

```bash
python transform_to_compliant_markdown.py \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-generation 16000 \
  --max-tokens-reasoning 4000 \
  --prompt-file prompt.md
```

### With Markdownlint Errors

```bash
python transform_to_compliant_markdown.py \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-generation 16000 \
  --max-tokens-reasoning 4000 \
  --prompt-file prompt.md \
  --markdownlint-errors '{"file.md": [{"lineNumber": 2, "ruleNames": ["MD013"]}]}'
```

### Command Line Arguments

- `--aws-region`: AWS region for Bedrock service (required)
- `--bedrock-model-id`: Bedrock model ID to use (required)
- `--max-tokens-generation`: Maximum tokens for content generation (required)
- `--max-tokens-reasoning`: Maximum tokens for extended thinking reasoning (required)
- `--prompt-file`: Path to prompt template file (required)
- `--markdownlint-errors`: JSON output from markdownlint-cli showing errors to fix (optional)

## Configuration

The `config.json` file contains default settings:

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

## How It Works

1. **File Reading**: The script reads the existing `CLAUDE.md` file from the current directory
2. **Prompt Generation**: Combines the markdown content with the prompt template and any markdownlint errors
3. **AI Processing**: Sends the content to AWS Bedrock Claude model with extended reasoning enabled
4. **Content Formatting**: Claude AI fixes markdownlint violations while preserving all original content
5. **File Writing**: Outputs the formatted content back to `CLAUDE.md`

## Prompt Template

The `prompt.md` file contains detailed instructions for Claude AI, including:

- Critical rules for content preservation
- Common markdownlint violation fixes
- Line breaking rules for long content
- Examples of proper formatting

Key formatting rules handled:
- **MD041**: Ensures first-line heading
- **MD013**: Breaks long lines with backslash continuation
- **MD022**: Adds blank lines around headings
- **MD012**: Removes consecutive blank lines
- **MD009**: Removes trailing whitespace
- **MD047**: Ensures single trailing newline

## Error Handling

The script includes robust error handling for:

- Missing `CLAUDE.md` file (exits with code 1)
- AWS API throttling (exponential backoff retry)
- Invalid Bedrock responses (graceful error reporting)
- Missing AWS credentials (boto3 exception handling)

## Testing

The project includes comprehensive tests:

- **Unit Tests** (`test_unit.py`): Configuration validation, function behavior, argument parsing
- **Integration Tests** (`test_integration.py`): AWS Bedrock client setup, file validation
- **End-to-End Tests** (`test_e2e.py`): Full workflow testing with temporary files

Run tests with:
```bash
pytest test/transform_to_compliant_markdown/
```

Note: E2E tests require valid AWS credentials and will be skipped if not available.

## AWS Permissions

Ensure your AWS credentials have the following permissions:

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
      "Resource": "arn:aws:bedrock:*:*:model/us.anthropic.claude-*"
    }
  ]
}
```

## Limitations

- Requires an existing `CLAUDE.md` file in the current working directory
- Designed specifically for Claude Sonnet 4 model format
- Processes only markdown files (not other document formats)
- Requires active AWS Bedrock service availability
