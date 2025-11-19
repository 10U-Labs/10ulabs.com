# README Generator for Infrastructure Projects

An AI-powered tool that automatically generates and maintains README.md files for infrastructure projects using AWS Bedrock and Claude AI.

## Overview

This tool uses AWS Bedrock's Claude Sonnet model to analyze project files and generate comprehensive, up-to-date README documentation. It can both check if existing README files need updates and generate new content automatically.

## Features

- **AI-Powered Analysis**: Uses Claude Sonnet 4 to understand project structure and generate relevant documentation
- **Dual Modes**: Check existing README currency or generate new content
- **Robust AWS Integration**: Built-in retry logic with exponential backoff for Bedrock API calls  
- **Multi-File Support**: Scans Python, JSON, YAML, Markdown, and text files
- **Template System**: Customizable prompts for different documentation needs
- **CI/CD Ready**: Outputs machine-readable results for GitHub Actions integration
- **Comprehensive Testing**: Full test suite with unit, integration, and end-to-end tests

## Configuration

The tool is configured via `config.json`:

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

### Check Mode
Determine if an existing README needs updating:

```bash
python readme.py --check \
  --project-dir /path/to/project \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --budget-tokens 4000 \
  --max-tokens 16000 \
  --prompt-check prompt_check.md \
  --prompt-update prompt_update.md \
  --output-file result.txt
```

### Update Mode
Generate or update the README file:

```bash
python readme.py --update \
  --project-dir /path/to/project \
  --aws-region us-east-1 \
  --bedrock-model-id us.anthropic.claude-sonnet-4-20250514-v1:0 \
  --budget-tokens 4000 \
  --max-tokens 16000 \
  --prompt-check prompt_check.md \
  --prompt-update prompt_update.md \
  --output-file result.txt
```

### Optional Test Directory
Include test files in the analysis:

```bash
python readme.py --update \
  --project-dir /path/to/project \
  --test-dir /path/to/tests \
  # ... other options
```

## Command Line Arguments

| Argument | Required | Description |
|----------|----------|-------------|
| `--check` | No* | Check if README is current |
| `--update` | No* | Update/generate README |
| `--project-dir` | Yes | Project directory path |
| `--aws-region` | Yes | AWS region for Bedrock |
| `--bedrock-model-id` | Yes | Bedrock model ID |
| `--budget-tokens` | Yes | Budget tokens for AI thinking |
| `--max-tokens` | Yes | Max tokens for model output |
| `--prompt-check` | Yes | Path to check prompt template |
| `--prompt-update` | Yes | Path to update prompt template |
| `--output-file` | Yes | Output file for results |
| `--test-dir` | No | Optional test directory to include |

*Either `--check` or `--update` must be specified.

## Prompt Templates

### Check Template (`prompt_check.md`)
Analyzes existing README files to determine if updates are needed. Returns JSON with update recommendation and reasoning.

### Update Template (`prompt_update.md`) 
Generates comprehensive README content based on project files. Explicitly excludes license information to avoid duplication with LICENSE.md files.

## File Discovery

The tool automatically discovers and analyzes:
- Python files (`*.py`)
- Configuration files (`*.json`, `*.yaml`, `*.yml`)
- Documentation files (`*.md`, `*.txt`)
- Lambda function files (`lambda/*.py`, `lambda/*/*.py`)
- Test files (when `--test-dir` specified)

Excludes existing README.md files to prevent circular references.

## Error Handling

- **Throttling**: Automatic retry with exponential backoff for Bedrock rate limits
- **Credentials**: Clear error messages for AWS authentication issues  
- **File Access**: Graceful handling of file read errors
- **API Responses**: Robust parsing of Bedrock responses with fallback logic

## Testing

Run the test suite:

```bash
# Unit tests
python -m pytest test/readme/test_unit.py

# Integration tests  
python -m pytest test/readme/test_integration.py

# End-to-end tests (requires AWS credentials)
python -m pytest test/readme/test_e2e.py
```

## Requirements

- Python 3.7+
- boto3
- AWS credentials configured
- Access to AWS Bedrock Claude models

## Architecture

The tool follows a modular design:

1. **File Discovery**: Scans project directories for relevant files
2. **Content Aggregation**: Combines file contents with metadata
3. **AI Analysis**: Sends structured prompts to Claude via Bedrock
4. **Response Processing**: Parses AI responses and handles errors
5. **Output Generation**: Creates README files or status reports

The retry mechanism ensures reliability against API rate limits, while the prompt template system allows customization for different project types.
