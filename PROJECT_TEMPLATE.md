# Project Template Design Pattern

This document describes the standard design pattern used for infrastructure
projects in this repository. Follow this template when creating new
self-standing infrastructure projects.

## Overview

Infrastructure projects follow a consistent pattern:

- **AWS CDK** for infrastructure as code (Python)
- **Serverless architecture** preferred over EC2/containers
- **Comprehensive testing** (unit, integration, E2E)
- **AI-generated README** using AWS Bedrock
- **GitHub Actions CI/CD** with full workflow automation

## Existing Projects Following This Pattern

- `cloudtrail_and_domain_name/` - CloudTrail logging and domain registration
- `gmail_email_provider/` - Gmail SMTP configuration via SES
- `api/self/` - API Gateway + Lambda REST API

Note: `auth_between_aws_and_github/` is unique and does NOT follow this
pattern (no CDK, different structure).

## Directory Structure

```text
<project_name>/
├── README.md                    # AI-generated, auto-updated
├── app.py                       # CDK app entry point
├── stack.py                     # CDK stack definition
├── config.json                  # Project configuration
├── cdk.json                     # CDK configuration
├── requirements.txt             # Python dependencies
├── readme.py                    # README generation script
├── lambda/                      # Lambda code (if applicable)
│   └── handler.py
├── test/                        # Test directory
│   ├── conftest.py             # pytest fixtures
│   ├── test_unit.py            # Unit tests
│   ├── test_integration.py     # Integration tests
│   └── test_e2e.py             # End-to-end tests
└── <optional_scripts>.py        # Project-specific utilities
```

## Required Files

### 1. config.json

Project configuration with AWS account, region, and project-specific settings.

**Standard structure:**

```json
{
  "aws": {
    "account_id": "123456789012",
    "region": "us-east-1",
    "bedrock": {
      "model_id": "us.anthropic.claude-sonnet-4-20250514-v1:0",
      "max_tokens_check": 200,
      "max_tokens_generate": 16000
    }
  },
  "project_specific_config": {
    ...
  }
}
```

**Required fields:**

- `aws.account_id` - AWS account ID
- `aws.region` - AWS region
- `aws.bedrock.model_id` - Bedrock model for README generation
- `aws.bedrock.max_tokens_check` - Max tokens for README check
- `aws.bedrock.max_tokens_generate` - Max tokens for README generation

### 2. cdk.json

Standard CDK configuration.

```json
{
  "app": "python3 app.py",
  "watch": {
    "include": ["**"],
    "exclude": [
      "README.md",
      "cdk.out",
      "requirements*.txt",
      "source.bat",
      "**/__init__.py",
      "**/__pycache__",
      "**/.pytest_cache",
      "**/.venv"
    ]
  },
  "context": {
    "@aws-cdk/aws-lambda:recognizeLayerVersion": true,
    "@aws-cdk/core:checkSecretUsage": true,
    "@aws-cdk/core:target-partitions": ["aws", "aws-cn"]
  }
}
```

### 3. requirements.txt

**Minimum required dependencies:**

```txt
aws-cdk-lib==2.150.0
constructs>=10.0.0,<11.0.0
boto3>=1.34.0
boto3-stubs[...]>=1.34.0
```

Add project-specific dependencies as needed (e.g., `requests` for HTTP calls).

### 4. app.py

CDK app entry point. Loads config.json and instantiates the stack.

**Standard structure:**

```python
import json
import os
import aws_cdk as cdk
from stack import <StackName>

app = cdk.App()

script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, 'config.json')

with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

env = cdk.Environment(
    account=config['aws']['account_id'],
    region=config['aws']['region']
)

<StackName>(app, '<StackName>', env=env, config=config)

app.synth()
```

### 5. stack.py

CDK stack definition. Contains all infrastructure resources.

**Standard structure:**

```python
import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    ...
)

class <StackName>(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str,
                 config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define infrastructure resources here
        ...
```

**Critical requirements:**

- NEVER enable S3 bucket versioning (`versioned=False`)
- Prefer serverless architecture (Lambda, API Gateway, DynamoDB, S3)
- Use EC2 only for build-time compute (AMI/Docker image building)
- NO comments in code (per CLAUDE.md coding standards)
- NO docstrings (per CLAUDE.md coding standards)

### 6. readme.py

Script to generate and check README using AWS Bedrock.

**Copy from existing project** (api/self/readme.py is the most recent).

**Key functions:**

- `read_source_files()` - Reads source files to include in context
- `check_readme_should_be_updated()` - Checks if README needs updating
- `generate_readme()` - Generates new README with Bedrock
- `main()` - CLI with `--check` and `--update` flags

**Prompt engineering requirements:**

- Include CRITICAL INSTRUCTIONS with verification checklist
- Add post-processing to ensure trailing newline
- Follow markdownlint rules (see api/self/readme.py lines 140-162)

### 7. lambda/handler.py (if applicable)

Lambda function handler.

**Standard structure:**

```python
import json

def handler(event, context):
    # Lambda logic here
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'message': 'Success'})
    }
```

### 8. test/conftest.py

pytest fixtures shared across tests.

**Standard structure:**

```python
import json
import os
import pytest
import boto3

@pytest.fixture(scope='session')
def config():
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(script_dir, 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture(scope='session')
def aws_region(config):
    return config['aws']['region']

@pytest.fixture(scope='session')
def lambda_client(aws_region):
    return boto3.client('lambda', region_name=aws_region)

# Add more fixtures as needed
```

### 9. test/test_unit.py

Unit tests - test code in isolation without AWS resources.

**Testing requirements:**

- Each test function has EXACTLY ONE assert (per CLAUDE.md)
- Test config.json structure
- Test CDK stack can be instantiated
- Test Lambda handlers with mock events
- Test utility functions

**Example:**

```python
def test_config_file_exists():
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
    assert os.path.exists(config_path)

def test_config_has_aws_account_id(config):
    assert 'account_id' in config['aws']
```

### 10. test/test_integration.py

Integration tests - test deployed AWS resources.

**Testing requirements:**

- Each test has EXACTLY ONE assert
- Uses boto3 to query AWS resources
- Verifies infrastructure exists and is configured correctly
- Requires AWS credentials in environment

**Example:**

```python
def test_lambda_function_exists(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [fn['FunctionName'] for fn in functions['Functions']]
    matching = [name for name in function_names if '<FunctionPrefix>' in name]
    assert len(matching) > 0
```

### 11. test/test_e2e.py

End-to-end tests - test live API endpoints and workflows.

**Testing requirements:**

- Each test has EXACTLY ONE assert
- Tests actual API endpoints
- Verifies end-to-end functionality
- May require deployed infrastructure (WARM state)

## GitHub Actions Workflow

Each project requires a corresponding workflow in `.github/workflows/`.

**Naming convention:** `<project_directory_name>.yml`

**Examples:**

- `api.yml` for `api/self/`
- `cloudtrail_and_domain_name.yml` for `cloudtrail_and_domain_name/`
- `gmail_email_provider.yml` for `gmail_email_provider/`

### Standard Workflow Structure

```yaml
name: <Descriptive workflow name>

on:
  push:
    branches:
      - main
    paths:
      - '<project_directory>/**'
      - '.github/workflows/<workflow_name>.yml'
  workflow_dispatch:
    inputs:
      dry_run:
        type: boolean
        required: false
        default: false
        description: 'Dry run mode (skip deployment, just test)'

concurrency:
  group: ${{ github.workflow_ref }}-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read
  id-token: write

jobs:
  performing-static-analysis:
    if: |
      github.event.inputs.dry_run != 'true' &&
      github.ref == 'refs/heads/main'
    name: Performing static analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install linting dependencies
        run: |
          pip install pylint mypy yamllint
          npm install -g jsonlint markdownlint-cli2
      - name: Install project dependencies for linting
        run: pip install -r <project_directory>/requirements.txt
      - name: Linting YAML files
        run: yamllint --config-data '{...}' .github/workflows/<workflow>.yml
      - name: Linting JSON files
        run: jsonlint -q <project_directory>/config.json
      - name: Linting Markdown documentation
        run: |
          if [ -f <project_directory>/README.md ]; then
            markdownlint-cli2 <project_directory>/README.md
          fi
      - name: Linting Python files
        run: |
          pylint <project_directory>/stack.py \
            --disable=line-too-long,missing-class-docstring,\
missing-function-docstring,missing-module-docstring,too-many-lines,\
too-many-locals \
            --fail-under=10.0
      - name: Static type checking with mypy
        run: mypy <project_directory> --exclude <project_directory>/test

  unit-testing:
    name: Unit testing
    needs: performing-static-analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install dependencies
        run: |
          pip install pytest
          pip install -r <project_directory>/requirements.txt
      - name: Run unit tests
        run: pytest <project_directory>/test/test_unit.py -v

  ensuring-infrastructure-in-desired-state:
    name: Ensuring infrastructure is in desired state
    needs: unit-testing
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Load configuration
        id: config
        run: |
          ACCOUNT_ID=$(jq -r '.aws.account_id' <project_directory>/config.json)
          REGION=$(jq -r '.aws.region' <project_directory>/config.json)
          echo "account_id=$ACCOUNT_ID" >> $GITHUB_OUTPUT
          echo "region=$REGION" >> $GITHUB_OUTPUT
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ steps.config.outputs.account_id }}:role/GitHubActionsRole
          aws-region: ${{ steps.config.outputs.region }}
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install CDK
        run: npm install -g aws-cdk
      - name: Install dependencies
        run: pip install -r <project_directory>/requirements.txt
      - name: CDK Bootstrap
        run: |
          cd <project_directory> && cdk bootstrap \
            aws://${{ steps.config.outputs.account_id }}/\
${{ steps.config.outputs.region }}
      - name: CDK Diff
        run: cd <project_directory> && cdk diff <StackName>
      - name: CDK Deploy
        run: |
          cd <project_directory> && cdk deploy <StackName> \
            --require-approval never

  integration-testing:
    name: Integration testing
    needs: ensuring-infrastructure-in-desired-state
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Load configuration
        id: config
        run: |
          ACCOUNT_ID=$(jq -r '.aws.account_id' <project_directory>/config.json)
          REGION=$(jq -r '.aws.region' <project_directory>/config.json)
          echo "account_id=$ACCOUNT_ID" >> $GITHUB_OUTPUT
          echo "region=$REGION" >> $GITHUB_OUTPUT
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ steps.config.outputs.account_id }}:role/GitHubActionsRole
          aws-region: ${{ steps.config.outputs.region }}
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install pytest boto3
      - name: Run integration tests
        run: pytest <project_directory>/test/test_integration.py -v

  e2e-testing:
    name: E2E testing
    needs: integration-testing
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Load configuration
        id: config
        run: |
          ACCOUNT_ID=$(jq -r '.aws.account_id' <project_directory>/config.json)
          REGION=$(jq -r '.aws.region' <project_directory>/config.json)
          echo "account_id=$ACCOUNT_ID" >> $GITHUB_OUTPUT
          echo "region=$REGION" >> $GITHUB_OUTPUT
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ steps.config.outputs.account_id }}:role/GitHubActionsRole
          aws-region: ${{ steps.config.outputs.region }}
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install pytest boto3
      - name: Run E2E tests
        run: pytest <project_directory>/test/test_e2e.py -v

  determining-if-readme-should-be-updated:
    name: Determining if README.md should be updated
    needs: e2e-testing
    outputs:
      readme_should_be_updated: \
${{ steps.check.outputs.readme_should_be_updated }}
    permissions:
      contents: read
      id-token: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Load configuration
        id: config
        run: |
          ACCOUNT_ID=$(jq -r '.aws.account_id' <project_directory>/config.json)
          REGION=$(jq -r '.aws.region' <project_directory>/config.json)
          echo "account_id=$ACCOUNT_ID" >> $GITHUB_OUTPUT
          echo "region=$REGION" >> $GITHUB_OUTPUT
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ steps.config.outputs.account_id }}:role/GitHubActionsRole
          aws-region: ${{ steps.config.outputs.region }}
      - name: Install boto3
        run: pip install boto3
      - name: Check if README needs update
        id: check
        run: |
          python <project_directory>/readme.py \
            --check \
            --aws-region "${{ steps.config.outputs.region }}" \
            --output-file "$GITHUB_OUTPUT"

  concluding-readme-should-be-updated:
    if: needs.determining-if-readme-should-be-updated.outputs.\
readme_should_be_updated == 'true'
    name: Concluding README.md should be updated
    needs: determining-if-readme-should-be-updated
    runs-on: ubuntu-latest
    steps:
      - run: 'true'

  concluding-readme-should-not-be-updated:
    if: needs.determining-if-readme-should-be-updated.outputs.\
readme_should_be_updated != 'true'
    name: Concluding README.md should not be updated
    needs: determining-if-readme-should-be-updated
    runs-on: ubuntu-latest
    steps:
      - run: 'true'

  updating-readme:
    name: Updating README.md
    needs: concluding-readme-should-be-updated
    permissions:
      contents: write
      id-token: write
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          token: ${{ secrets.GITHUB_TOKEN }}
      - name: Load configuration
        id: config
        run: |
          ACCOUNT_ID=$(jq -r '.aws.account_id' <project_directory>/config.json)
          REGION=$(jq -r '.aws.region' <project_directory>/config.json)
          echo "account_id=$ACCOUNT_ID" >> $GITHUB_OUTPUT
          echo "region=$REGION" >> $GITHUB_OUTPUT
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::${{ steps.config.outputs.account_id }}:role/GitHubActionsRole
          aws-region: ${{ steps.config.outputs.region }}
      - name: Install boto3
        run: pip install boto3
      - name: Update README with Bedrock
        run: |
          python <project_directory>/readme.py \
            --update \
            --aws-region "${{ steps.config.outputs.region }}"
      - name: Commit and push README if changed
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add <project_directory>/README.md
          if git diff --cached --quiet; then
            echo "No changes to README.md"
          else
            git commit -m "Update <project> README.md [skip ci]"
            git push
          fi
```

## Prerequisites Documentation

When documenting prerequisites in the auto-generated README, use CORRECT
requirements:

**CORRECT:**

```markdown
## Prerequisites

- AWS CDK v2.x installed (`npm install -g aws-cdk`)
- Python 3.8 or higher
- AWS credentials configured (environment variables or ~/.aws/credentials)
- Node.js 20.x (required by AWS CDK)
```

**INCORRECT (DO NOT USE):**

```markdown
## Prerequisites

- AWS CLI configured with appropriate permissions  # WRONG - NOT NEEDED
```

**Why AWS CLI is NOT required:**

- Infrastructure deployment uses AWS CDK CLI (Node.js), not AWS CLI
- Python code uses boto3 (AWS SDK for Python), not AWS CLI
- AWS credentials come from environment variables or ~/.aws/credentials
- No workflow steps use `aws` commands

**When AWS CLI IS actually needed:**

- Only if you explicitly call `aws` commands in scripts
- Very rare - most AWS operations should use boto3 or CDK

## Static Analysis Requirements

Per CLAUDE.md coding standards:

**Pylint:**

```bash
pylint <files> \
  --disable=line-too-long,missing-class-docstring,\
missing-function-docstring,missing-module-docstring,too-many-lines,\
too-many-locals \
  --fail-under=10.0
```

**Mypy:**

```bash
mypy <directory> --exclude <directory>/test
```

**YAML linting:**

```bash
yamllint --config-data '{extends: default, rules: {line-length: \
{max: 200, level: warning}, document-start: disable, truthy: \
{allowed-values: ["true", "false", "on"]}}}' <file>.yml
```

**JSON linting:**

```bash
jsonlint -q <file>.json
```

**Markdown linting:**

```bash
markdownlint-cli2 <file>.md
```

## Testing Requirements

Per CLAUDE.md coding standards:

**Each test must have EXACTLY ONE assert:**

```python
# GOOD
def test_bucket_exists():
    buckets = s3_client.list_buckets()
    bucket_names = [b['Name'] for b in buckets['Buckets']]
    assert 'my-bucket' in bucket_names

def test_bucket_has_encryption():
    encryption = s3_client.get_bucket_encryption(Bucket='my-bucket')
    rule = encryption['Rules'][0]
    assert rule['ApplyServerSideEncryptionByDefault']['SSEAlgorithm'] == \
'AES256'

# BAD - multiple asserts
def test_bucket_properties():
    buckets = s3_client.list_buckets()
    assert len(buckets['Buckets']) > 0  # WRONG
    encryption = s3_client.get_bucket_encryption(Bucket='my-bucket')
    assert encryption is not None  # WRONG
```

## Coding Standards

Per CLAUDE.md:

**NO COMMENTS of any kind:**

- No inline comments (`# comment`)
- No docstrings (`"""..."""`)
- No pylint disable comments
- No type: ignore comments
- No mypy ignore comments

**If linters fail, fix the code - don't disable warnings with comments.**

**S3 Buckets must have versioning disabled:**

```python
# CORRECT
bucket = s3.Bucket(
    self, 'MyBucket',
    versioned=False  # REQUIRED
)

# WRONG
bucket = s3.Bucket(
    self, 'MyBucket',
    versioned=True  # NEVER DO THIS
)
```

**Prefer serverless architecture:**

- Use Lambda, API Gateway, DynamoDB, S3, etc.
- Use EC2 only for build-time compute (AMI/Docker images)
- Never use EC2 for application hosting when serverless alternatives exist

## Creating a New Project

1. Create project directory: `<project_name>/`
2. Copy structure from existing project (e.g., `api/self/`)
3. Update `config.json` with project-specific configuration
4. Update `stack.py` with infrastructure resources
5. Update `app.py` to use correct stack name
6. Copy `readme.py` from `api/self/` (most recent version)
7. Create `lambda/handler.py` if needed
8. Create test files: `test_unit.py`, `test_integration.py`, `test_e2e.py`
9. Create GitHub workflow: `.github/workflows/<project_name>.yml`
10. Run static analysis and tests locally (per CLAUDE.md pre-push checklist)
11. Commit and push to trigger workflow

## LLM-Assisted Project Generation

This template is designed to be used by LLMs (like Claude) to automatically
generate new infrastructure projects. An LLM should be able to:

1. Read this template document
2. Understand the requirements and patterns
3. Generate a complete project structure
4. Follow all coding standards and testing requirements
5. Create the corresponding GitHub Actions workflow
6. Generate appropriate README using the readme.py pattern

The template provides enough structure and examples that an LLM can create a
fully functional, test-covered, CI/CD-integrated infrastructure project with
minimal human intervention.
