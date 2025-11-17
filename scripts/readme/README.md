# README Generator

An AI-powered README generator that uses AWS Bedrock to automatically create and maintain README documentation for software projects.

## Overview

This tool analyzes project files and uses Claude (via AWS Bedrock) to generate comprehensive README documentation. It can both check if an existing README needs updating and generate new README content based on the current state of your project files.

## Features

- **Intelligent README Generation**: Uses AWS Bedrock's Claude model to analyze project files and generate comprehensive documentation
- **Smart Update Detection**: Checks if existing README files are current and accurate
- **Multi-file Analysis**: Scans Python, JSON, Markdown, YAML, and text files across the project
- **Retry Logic**: Built-in retry mechanism with exponential backoff for API throttling
- **GitHub Actions Ready**: Designed to work seamlessly in CI/CD pipelines

## Prerequisites

- Python 3.x
- AWS account with Bedrock access
- Appropriate AWS credentials configured
- Access to Claude Sonnet model in AWS Bedrock

## Configuration

The tool uses a `config.json` file for AWS and Bedrock settings:

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

## Usage

### Check if README needs updating

```bash
python readme.py --check \
  --project-dir /path/to/project \
  --aws-region us-east-1 \
  --output-file output.txt \
  --bedrock-model-id "us.anthropic.claude-sonnet-4-20250514-v1:0" \
  --max-tokens-reasoning 4000 \
  --max-tokens-generation 16000 \
  --prompt-check prompt_check.md \
  --prompt-update prompt_update.md
```

### Generate/Update README

```bash
python readme.py --update \
  --project-dir /path/to/project \
  --aws-region us-east-1 \
  --output-file output.txt \
  --bedrock-model-id "us.anthropic.claude-sonnet-4-20250514-v1:0" \
  --max-tokens-reasoning 4000 \
  --max-tokens-generation 16000 \
  --prompt-check prompt_check.md \
  --prompt-update prompt_update.md
```

## Command Line Arguments

- `--check`: Check if the current README is up to date
- `--update`: Generate or update the README file
- `--project-dir`: Path to the project directory to analyze
- `--aws-region`: AWS region for Bedrock service
- `--output-file`: Output file for check results (used by GitHub Actions)
- `--bedrock-model-id`: Bedrock model ID to use for generation
- `--max-tokens-reasoning`: Maximum tokens for reasoning phase
- `--max-tokens-generation`: Maximum tokens for content generation
- `--prompt-check`: Path to the check prompt template file
- `--prompt-update`: Path to the update prompt template file

## File Analysis

The tool automatically discovers and analyzes these file types:
- Python files (`.py`)
- JSON configuration files (`.json`)
- Markdown files (`.md`)
- YAML files (`.yaml`, `.yml`)
- Text files (`.txt`)
- Lambda function files in `lambda/` directories

## Prompt Templates

The tool uses two prompt templates:

### prompt_check.md
Used to determine if an existing README needs updating. Returns a JSON response indicating whether updates are needed and the reasoning.

### prompt_update.md
Used to generate new README content based on project files. Includes instructions to avoid duplicating license information since the repository has a separate LICENSE.md file.

## Error Handling

- **Throttling**: Automatic retry with exponential backoff for API rate limits
- **File Access**: Graceful handling of missing or unreadable files
- **Network Issues**: Retry logic for transient network problems
- **Validation**: Input validation for required parameters and file paths

## Dependencies

- `boto3`: AWS SDK for Python
- `botocore`: Core functionality for AWS SDK
- Standard library modules: `argparse`, `json`, `logging`, `os`, `random`, `sys`, `time`, `glob`

## Architecture

The tool follows a modular design:
1. **File Discovery**: Scans project directory for relevant files
2. **Content Analysis**: Reads and combines file contents
3. **AI Processing**: Uses Bedrock to analyze and generate documentation
4. **Output Generation**: Creates formatted README content
5. **Error Recovery**: Handles API limits and network issues gracefully
