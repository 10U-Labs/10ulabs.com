# README Generator

An AWS Bedrock-powered tool for automatically generating and maintaining README files for software projects using AI.

## Overview

This tool uses AWS Bedrock and Claude AI models to automatically generate comprehensive README files by analyzing project source code, configuration files, and documentation. It can both check if existing README files need updates and generate new content based on the current state of your project.

## Features

- **Automatic Project Analysis**: Scans directories for Python files, configuration files (JSON, YAML), and documentation
- **AI-Powered Generation**: Uses AWS Bedrock with Claude Sonnet models for intelligent README generation
- **Smart Update Detection**: Determines when existing README files need refreshing
- **Robust Error Handling**: Includes retry logic with exponential backoff for API calls
- **CI/CD Integration**: Designed for GitHub Actions and other automation workflows
- **Comprehensive Testing**: Full test coverage including unit, integration, and end-to-end tests

## Configuration

The tool uses a `config.json` file for AWS and Bedrock configuration:

```json
{
  "aws": {
    "account_id": 781581267945,
    "region": "us-east-1",
    "bedrock": {
      "budget_tokens": 10000,
      "max_tokens": 64000,
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0"
    }
  }
}
```

## Usage

### Check if README needs updating

```bash
python readme.py --check \
  --project-dir /path/to/project \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --budget-tokens 10000 \
  --max-tokens 64000 \
  --prompt-check prompt_check.md \
  --prompt-update prompt_update.md \
  --output-file result.txt
```

### Generate/update README

```bash
python readme.py --update \
  --project-dir /path/to/project \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --budget-tokens 10000 \
  --max-tokens 64000 \
  --prompt-check prompt_check.md \
  --prompt-update prompt_update.md \
  --output-file result.txt
```

### Command Line Options

- `--check`: Check if README needs updating (returns boolean result)
- `--update`: Generate or update the README file
- `--project-dir`: Path to the project directory to analyze
- `--test-dir`: Optional path to test directory to include in analysis
- `--aws-region`: AWS region for Bedrock service
- `--bedrock-model-id`: Bedrock model identifier to use
- `--budget-tokens`: Token budget for extended AI thinking
- `--max-tokens`: Maximum tokens for model output
- `--prompt-check`: Path to check prompt template file
- `--prompt-update`: Path to update prompt template file
- `--output-file`: Output file for results (required for GitHub Actions integration)

## File Discovery

The tool automatically discovers and analyzes these file types:

- Python files (`*.py`)
- Configuration files (`*.json`, `*.yaml`, `*.yml`)
- Documentation files (`*.md`, `*.txt`)
- Lambda function files (`lambda/*.py`, `lambda/*/*.py`)

## Prerequisites

- Python 3.6+
- AWS credentials configured (IAM role, access keys, or OIDC)
- AWS Bedrock access with appropriate model permissions
- `boto3` library installed

## IAM Permissions

Your AWS credentials need the following permissions:

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
      "Resource": "arn:aws:bedrock:*::foundation-model/us.anthropic.claude-sonnet-4-*"
    }
  ]
}
```

## Prompt Templates

The tool uses two markdown prompt templates:

- `prompt_check.md`: Evaluates whether an existing README needs updates
- `prompt_update.md`: Generates new README content based on project analysis

Both templates use variable substitution with `{project_files}` and `{current_readme}` placeholders.

## Error Handling

- Automatic retry with exponential backoff for Bedrock API throttling
- Random jitter to prevent thundering herd problems
- Comprehensive logging for debugging
- Graceful handling of missing files and directories

## Testing

Run the test suite:

```bash
# Unit tests
pytest test/readme/test_unit.py

# Integration tests (requires AWS credentials)
pytest test/readme/test_integration.py

# End-to-end tests (requires AWS credentials)
pytest test/readme/test_e2e.py
```

The tests include:
- Unit tests with mocked AWS services
- Integration tests validating AWS Bedrock connectivity
- End-to-end tests with real API calls
- File handling and prompt template validation

## Architecture

The tool consists of several key components:

- **File Discovery**: Recursively scans project directories using glob patterns
- **Content Aggregation**: Combines all discovered files into a structured format
- **AI Processing**: Sends content to AWS Bedrock for analysis and generation
- **Output Management**: Writes results to files and handles formatting

## Limitations

- Requires active AWS credentials and Bedrock access
- Token limits may affect processing of very large codebases
- API costs apply for Bedrock usage
- Generated content quality depends on source code organization and comments
