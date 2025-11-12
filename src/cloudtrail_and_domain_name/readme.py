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
        'lambda/handler.py',
        'lambda/cfnresponse.py'
    ]

    for file_path in files_to_read:
        full_path = os.path.join(script_dir, file_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                source_files[file_path] = f.read()
        except IOError as e:
            logging.error(f"Failed to read {file_path}: {e}")
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
3. Inaccurately describes the infrastructure components (CloudTrail, S3 buckets, Lambda, domain registration)
4. Missing or incorrect documentation of Lambda function behavior and purpose
5. Fails to explain the CloudFormation custom resource pattern used
6. Incorrect usage instructions for the CDK stack
7. Missing key resources created by the stack
8. Outdated command examples or file paths
9. Missing or incorrect configuration details
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
        logging.info(f"Bedrock assessment: README is {'current' if is_current else 'not current'}")
        return is_current
    except Exception as e:
        logging.error(f"Failed to check README with Bedrock: {e}")
        sys.exit(1)

def generate_readme(bedrock_client, source_code: str, model_id: str, max_tokens: int) -> str:
    prompt = f"""You are a technical documentation expert. Generate a comprehensive README.md file for the following AWS CDK infrastructure code that manages CloudTrail and domain name registration.

<source_code>
{source_code}
</source_code>

Create a professional README that includes:
1. Title and overview of what this infrastructure does
2. Purpose and key features
3. Resources created:
   - CloudTrail configuration
   - S3 buckets (CloudTrail logs, access logs)
   - Lambda function for domain registration
   - CloudFormation custom resource pattern
4. Prerequisites and requirements
5. Usage instructions (how to deploy the stack)
6. Architecture explanation:
   - How CloudTrail is configured
   - How domain registration works via Lambda
   - Custom resource lifecycle
7. Configuration details
8. Testing approach
9. Security considerations (bucket policies, encryption, etc.)
10. Troubleshooting tips

Format the README in clean, professional markdown. Be comprehensive but concise. Use code blocks for examples.
Generate ONLY the README content, starting with the title. Do not include any preamble or explanation."""

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
        logging.info("Generated new README content")
        return readme_content
    except Exception as e:
        logging.error(f"Failed to generate README with Bedrock: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Manage README.md for CloudTrail and Domain Name infrastructure'
    )
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check if README is current and write result to output file'
    )
    parser.add_argument(
        '--update',
        action='store_true',
        help='Generate and update README.md'
    )
    parser.add_argument(
        '--output-file',
        help='File to write check result (for GitHub Actions output)'
    )
    parser.add_argument(
        '--aws-region',
        required=True,
        help='AWS region for Bedrock'
    )
    parser.add_argument(
        '--bedrock-model-id',
        help='Bedrock model ID to use'
    )
    parser.add_argument(
        '--max-tokens-check',
        type=int,
        help='Max tokens for README check'
    )
    parser.add_argument(
        '--max-tokens-generate',
        type=int,
        help='Max tokens for README generation'
    )

    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except IOError as e:
        logging.error(f"Failed to read config.json: {e}")
        sys.exit(1)

    bedrock_model_id = args.bedrock_model_id or config.get('bedrock', {}).get('model_id', 'us.anthropic.claude-sonnet-4-20250514-v1:0')
    max_tokens_check = args.max_tokens_check or config.get('bedrock', {}).get('max_tokens_check', 200)
    max_tokens_generate = args.max_tokens_generate or config.get('bedrock', {}).get('max_tokens_generate', 16000)

    if not args.check and not args.update:
        logging.error("Either --check or --update must be specified")
        sys.exit(1)

    if args.check and args.update:
        logging.error("Cannot specify both --check and --update")
        sys.exit(1)

    readme_path = os.path.join(script_dir, 'README.md')

    logging.info("Reading source files...")
    source_code = read_source_files()

    logging.info("Initializing Bedrock client...")
    try:
        bedrock_client = boto3.client('bedrock-runtime', region_name=args.aws_region)
    except Exception as e:
        logging.error(f"Failed to create Bedrock client: {e}")
        sys.exit(1)

    if args.check:
        current_readme = ""
        if os.path.exists(readme_path):
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    current_readme = f.read()
            except IOError as e:
                logging.error(f"Failed to read README: {e}")
                sys.exit(1)

        logging.info("Checking if README is current via Bedrock...")
        readme_is_current = check_readme_is_current(bedrock_client, source_code, current_readme, bedrock_model_id, max_tokens_check)

        print(readme_is_current)

        if args.output_file:
            try:
                with open(args.output_file, 'a', encoding='utf-8') as f:
                    f.write(f'readme_is_current={str(readme_is_current).lower()}\n')
                logging.info(f"Wrote readme_is_current={readme_is_current} to {args.output_file}")
            except IOError as e:
                logging.error(f"Failed to write output file: {e}")
                sys.exit(1)

    elif args.update:
        logging.info("Generating updated README via Bedrock...")
        new_readme = generate_readme(bedrock_client, source_code, bedrock_model_id, max_tokens_generate)

        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(new_readme)
            logging.info(f"Updated README written to {readme_path}")
            print(f"README updated successfully: {readme_path}")
        except IOError as e:
            logging.error(f"Failed to write README: {e}")
            sys.exit(1)

if __name__ == '__main__':
    main()
