# Markdown Compliance Formatter

A Python tool that automatically formats Markdown files to comply with markdownlint rules using AWS Bedrock's Claude AI model.

## Overview

This tool takes Markdown files with markdownlint violations and uses AWS Bedrock to intelligently fix formatting issues while preserving all original content. It's designed to handle common markdownlint violations such as line length limits, heading spacing, trailing whitespace, and more.

## Features

- **AI-Powered Formatting**: Uses Claude Sonnet 4 via AWS Bedrock for intelligent Markdown formatting
- **Preserve Content**: Maintains exact content meaning while fixing formatting violations
- **Comprehensive Rule Support**: Handles all common markdownlint violations (MD041, MD013, MD022, MD012, MD009, MD047, etc.)
- **Retry Logic**: Built-in exponential backoff and retry handling for AWS API throttling
- **Extended Reasoning**: Supports Claude's extended thinking mode for complex formatting decisions
- **Flexible Input**: Works with any Markdown file, not just specific filenames

## Requirements

- Python 3.7+
- AWS credentials configured (via IAM roles, environment variables, or AWS CLI)
- Access to AWS Bedrock with Claude Sonnet 4 model
- Required Python packages:
  - `boto3`
  - `botocore`

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install boto3 botocore
   ```
3. Ensure AWS credentials are configured with Bedrock access

## Usage

### Basic Usage

Format a Markdown file without specific markdownlint errors:

```bash
python transform_to_compliant_markdown.py \
  --file README.md \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-generation 16000 \
  --max-tokens-reasoning 4000 \
  --prompt-file prompt.md
```

### With Markdownlint Errors

Format a file with specific markdownlint violations to fix:

```bash
python transform_to_compliant_markdown.py \
  --file CLAUDE.md \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --max-tokens-generation 16000 \
  --max-tokens-reasoning 4000 \
  --prompt-file prompt.md \
  --markdownlint-errors '{"file.md": [{"lineNumber": 2, "ruleNames": ["MD013"]}]}'
```

### Command Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--file` | Yes | Path to the Markdown file to format |
| `--aws-region` | Yes | AWS region for Bedrock service |
| `--bedrock-model-id` | Yes | Bedrock model ID to use |
| `--max-tokens-generation` | Yes | Maximum tokens for content generation |
| `--max-tokens-reasoning` | Yes | Maximum tokens for extended reasoning |
| `--prompt-file` | Yes | Path to the prompt template file |
| `--markdownlint-errors` | No | JSON string of markdownlint violations to fix |

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

1. **Input Processing**: Reads the target Markdown file and optional markdownlint error report
2. **Prompt Generation**: Uses the `prompt.md` template to create a detailed formatting prompt
3. **AI Processing**: Sends the content to Claude via AWS Bedrock with specific formatting instructions
4. **Output Generation**: Writes the formatted content back to the original file
5. **Validation**: Ensures the output ends with a proper newline character

## Supported Markdownlint Rules

The tool handles common markdownlint violations including:

- **MD041**: Missing first-line heading
- **MD013**: Line length violations (80 character limit)
- **MD022**: Missing blank lines around headings
- **MD012**: Multiple consecutive blank lines
- **MD009**: Trailing whitespace
- **MD047**: Missing single trailing newline

## Error Handling

- **File Not Found**: Exits with code 1 if the target Markdown file doesn't exist
- **AWS Throttling**: Implements exponential backoff retry logic for API throttling
- **Invalid Response**: Validates Bedrock response structure and exits gracefully on errors
- **Network Issues**: Handles AWS API errors with appropriate error messages

## Testing

The project includes comprehensive tests:

- **Unit Tests**: Test individual functions and error handling
- **Integration Tests**: Verify configuration and file structure
- **End-to-End Tests**: Full workflow testing with AWS Bedrock (requires credentials)

Run tests with:
```bash
pytest test/transform_to_compliant_markdown/
```

## Project Structure

```
scripts/transform_to_compliant_markdown/
├── config.json                           # Default configuration
├── prompt.md                            # AI prompt template
├── transform_to_compliant_markdown.py   # Main script
└── test/
    ├── test_unit.py                     # Unit tests
    ├── test_integration.py              # Integration tests
    └── test_e2e.py                      # End-to-end tests
```

## AWS Permissions

The tool requires the following AWS permissions:

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
      "Resource": "arn:aws:bedrock:*:*:model/us.anthropic.claude-sonnet-4-*"
    }
  ]
}
```

## Contributing

1. Ensure all tests pass before submitting changes
2. Add tests for new functionality
3. Follow the existing code style and structure
4. Update documentation for any new features or changes
