#!/usr/bin/env python3
import argparse
import json
import logging
import os
import sys
import boto3

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stderr
)

def read_source_files() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    source_files = {}

    files_to_read = [
        'stack.py',
        'lambda/handler.py'
    ]

    for file_path in files_to_read:
        full_path = os.path.join(script_dir, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source_files[file_path] = f.read()
        except IOError as e:
            logging.error("Failed to read %s: %s", file_path, e)
            sys.exit(1)

    combined = ""
    for file_path, content in source_files.items():
        combined += f"\n\n{'='*60}\nFile: {file_path}\n{'='*60}\n{content}"

    return combined

def check_readme_is_current(bedrock_client, source_code: str, current_readme: str, model_id: str, max_tokens: int) -> bool:
    if not current_readme or not current_readme.strip():
        logging.info("README is empty or missing")
        return False

    prompt = f"""You are a technical documentation expert. Your task is to determine if a README file is current and accurate for the given AWS CDK infrastructure code.

<source_code>
{source_code}
</source_code>

<current_readme>
{current_readme}
</current_readme>

Check if the README has ANY issues, including but not limited to:
1. Title doesn't match actual infrastructure name or uses outdated terminology
2. Inconsistent or outdated terminology throughout the document
3. Inaccurately describes the infrastructure components (API Gateway, Lambda, ACM certificate, Route53)
4. Missing or incorrect documentation of Lambda function endpoints and behavior
5. Fails to explain the API Gateway REST API configuration
6. Incorrect usage instructions for the CDK stack
7. Missing key resources created by the stack
8. Outdated command examples or file paths
9. Missing or incorrect API endpoint documentation
10. Any other inaccuracies, inconsistencies, or outdated information

Is the README current and accurate? Respond with ONLY "true" or "false"."""

    try:
        response = bedrock_client.converse(
            modelId=model_id,
            messages=[{
                'role': 'user',
                'content': [{'text': prompt}]
            }],
            inferenceConfig={
                'maxTokens': max_tokens
            }
        )

        answer = response['output']['message']['content'][0]['text'].strip().lower()
        is_current = answer.startswith('true')
        status = 'current' if is_current else 'not current'
        logging.info("Bedrock assessment: README is %s", status)
        return is_current
    except (KeyError, IndexError, TypeError) as e:
        logging.error("Failed to check README with Bedrock: %s", e)
        sys.exit(1)

def generate_readme(bedrock_client, source_code: str, model_id: str, max_tokens: int) -> str:
    prompt = f"""You are a technical documentation expert. Generate a comprehensive README.md file for the following AWS CDK infrastructure code that creates an API Gateway REST API with Lambda backend.

<source_code>
{source_code}
</source_code>

Create a professional README that includes:
1. Title and overview of what this infrastructure does
2. Purpose and key features
3. Resources created:
   - API Gateway REST API with custom domain
   - Lambda function for API endpoints
   - ACM certificate for SSL/TLS
   - Route53 A record for subdomain
   - CloudWatch logs for API and Lambda
4. Prerequisites and requirements
5. API Endpoints:
   - GET /health - health check endpoint
   - POST /v1/echo - echo endpoint
6. Deployment instructions
7. Configuration details (subdomain, parent domain)
8. Testing the API
9. Architecture notes (serverless, CORS enabled, access logging)

Format the output as proper Markdown with appropriate headers, code blocks, and sections. Be specific about what each resource does and why it exists. Do not include any preamble or explanation - output ONLY the README.md content."""

    try:
        response = bedrock_client.converse(
            modelId=model_id,
            messages=[{
                'role': 'user',
                'content': [{'text': prompt}]
            }],
            inferenceConfig={
                'maxTokens': max_tokens
            }
        )

        readme_content = response['output']['message']['content'][0]['text']
        logging.info("Successfully generated README with Bedrock")
        return readme_content
    except (KeyError, IndexError, TypeError) as e:
        logging.error("Failed to generate README with Bedrock: %s", e)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Generate or check README for API infrastructure')
    parser.add_argument('--check', action='store_true', help='Check if README is current')
    parser.add_argument('--update', action='store_true', help='Update README')
    parser.add_argument('--aws-region', required=True, help='AWS region')
    parser.add_argument('--output-file', help='Output file for check result (for GitHub Actions)')
    parser.add_argument('--bedrock-model-id', help='Bedrock model ID to use')
    parser.add_argument('--max-tokens-check', type=int, help='Max tokens for README check')
    parser.add_argument('--max-tokens-generate', type=int, help='Max tokens for README generation')
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except IOError as e:
        logging.error("Failed to read config.json: %s", e)
        sys.exit(1)

    bedrock_model_id = args.bedrock_model_id or config.get('bedrock', {}).get('model_id', 'us.anthropic.claude-sonnet-4-20250514-v1:0')
    max_tokens_check = args.max_tokens_check or config.get('bedrock', {}).get('max_tokens_check', 200)
    max_tokens_generate = args.max_tokens_generate or config.get('bedrock', {}).get('max_tokens_generate', 16000)

    if not args.check and not args.update:
        logging.error("Must specify either --check or --update")
        sys.exit(1)

    bedrock_client = boto3.client('bedrock-runtime', region_name=args.aws_region)
    source_code = read_source_files()
    readme_path = os.path.join(script_dir, 'README.md')

    if args.check:
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                current_readme = f.read()
        except FileNotFoundError:
            current_readme = ""

        is_current = check_readme_is_current(bedrock_client, source_code, current_readme, bedrock_model_id, max_tokens_check)

        if args.output_file:
            with open(args.output_file, 'a', encoding='utf-8') as f:
                f.write(f"readme_is_current={'true' if is_current else 'false'}\n")

        sys.exit(0 if is_current else 1)

    elif args.update:
        new_readme = generate_readme(bedrock_client, source_code, bedrock_model_id, max_tokens_generate)

        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_readme)

        logging.info("README updated at %s", readme_path)
        sys.exit(0)

if __name__ == '__main__':
    main()
