# AI Documentation Assistant

An intelligent documentation management system that leverages AWS Bedrock to automatically generate and maintain technical documentation. The system uses advanced AI models to analyze project files and create comprehensive README documentation with automated accuracy checking.

## Features

- **Automated Documentation Generation**: Creates comprehensive README files from project source code
- **Documentation Accuracy Validation**: Intelligent checking system to verify documentation correctness
- **AWS Bedrock Integration**: Leverages Claude Sonnet 4 model for high-quality content generation
- **Template-Based Processing**: Uses structured prompts for consistent documentation output
- **JSON Configuration Management**: Flexible configuration system for AWS services and model parameters

## Configuration

The system is configured through `config.json` with the following structure:

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

- **AWS Account ID**: `781581267945`
- **AWS Region**: `us-east-1` 
- **AI Model**: Claude Sonnet 4 (April 2025 version)
- **Token Limits**:
  - Reasoning: 4,000 tokens
  - Generation: 16,000 tokens

## System Components

### Documentation Validation (`prompt_check.md`)
- Analyzes existing README files for accuracy and completeness
- Checks for common documentation issues and inconsistencies
- Returns structured JSON responses indicating whether updates are needed
- Specifically validates against license duplication (prevents README from including license sections when LICENSE.md exists)

### Documentation Generation (`prompt_update.md`)
- Generates comprehensive README files from project source code
- Ensures factual accuracy through verification against project files
- Excludes license sections when separate LICENSE.md files exist
- Produces clean, formatted Markdown output

## Usage

The system processes project files and generates documentation using two main workflows:

1. **Validation Workflow**: Check if existing documentation needs updates
2. **Generation Workflow**: Create new or updated README documentation

Both workflows use the AWS Bedrock Claude Sonnet 4 model with the specified token limits and configuration parameters.

## Requirements

- AWS Account with Bedrock access
- Claude Sonnet 4 model availability in us-east-1 region
- Proper AWS credentials and permissions for Bedrock service access

## Architecture

The system follows a template-driven approach where:
- Project files are analyzed and processed
- AI prompts are structured for specific documentation tasks
- AWS Bedrock handles the AI processing with configured parameters
- Output is validated and formatted as clean Markdown documentation
