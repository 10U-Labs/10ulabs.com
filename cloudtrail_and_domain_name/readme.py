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
            logging.error("Failed to read %s: %s", file_path, e)
            sys.exit(1)

    combined = ""
    for file_path, content in source_files.items():
        combined += f"\n\n{'='*60}\nFile: {file_path}\n{'='*60}\n{content}"

    return combined

def check_readme_should_be_updated(bedrock_client, source_code: str, current_readme: str, model_id: str, max_tokens: int) -> bool:
    if not current_readme or not current_readme.strip():
        logging.info("README is empty or missing - should be updated")
        return True

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

Respond with ONLY a JSON object in this exact format:
{{
  "readme_should_be_updated": true,
  "reasoning": "Explain your thought process and what issues you found, if any"
}}

or

{{
  "readme_should_be_updated": false,
  "reasoning": "Explain your thought process and confirm the README is current"
}}

Do not include any other text or formatting outside the JSON object."""

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

        answer_text = response['output']['message']['content'][0]['text'].strip()
        try:
            result = json.loads(answer_text)
            should_be_updated = bool(result.get('readme_should_be_updated', False))
            reasoning = result.get('reasoning', 'No reasoning provided')
            logging.info("Bedrock reasoning: %s", reasoning)
            status = 'be updated' if should_be_updated else 'not be updated'
            logging.info("Bedrock assessment: README should %s", status)
            return should_be_updated
        except json.JSONDecodeError as e:
            logging.warning("Failed to parse JSON response from Bedrock: %s", e)
            logging.warning("Raw response: %s", answer_text)
            should_be_updated = answer_text.lower().startswith('true')
            status = 'be updated' if should_be_updated else 'not be updated'
            logging.info("Bedrock assessment (fallback): README should %s", status)
            return should_be_updated
    except (boto3.exceptions.Boto3Error, KeyError, ValueError) as e:
        logging.error("Failed to check README with Bedrock: %s", e)
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

IMPORTANT: Do NOT include a "License" section. The repository already has a LICENSE.md file, so the README must not duplicate licensing information.

Format the README in clean, professional markdown that complies with all markdownlint rules:
- Keep all lines under 80 characters
- Always add blank lines before and after lists
- Always add blank lines before and after code blocks
- Indent code blocks with 3 spaces when inside ordered/unordered lists
- Use proper heading levels (# ## ### ####), never use bold text as headings
- Add language specifiers to all code blocks (```bash, ```python, ```json, etc.)
- Wrap bare URLs in angle brackets (<https://example.com>)
- End file with exactly one newline character
- Use proper table formatting with spaces around pipes (| Column 1 | Column 2 |)

CRITICAL INSTRUCTIONS:
1. Generate the README content first
2. Before outputting, verify EACH requirement using this checklist:

   FACTUAL ACCURACY (verify against source code):
   - [ ] Prerequisites match actual dependencies (check requirements.txt)
   - [ ] NO mention of AWS CLI (uses boto3, not awscli)
   - [ ] Correct: AWS CDK CLI, Python, Node.js, AWS credentials
   - [ ] Resource descriptions match stack.py definitions
   - [ ] Lambda handler implementation matches handler.py
   - [ ] Configuration examples match config.json structure

   FORMATTING (markdownlint compliance):
   - [ ] All lines under 80 characters
   - [ ] Blank lines before/after lists
   - [ ] Blank lines before/after code blocks
   - [ ] Code blocks indented with 3 spaces when inside lists
   - [ ] All headings use # syntax (not bold)
   - [ ] All code blocks have language specifiers
   - [ ] All bare URLs wrapped in angle brackets
   - [ ] File ends with exactly one newline
   - [ ] No License section included

3. If any check fails, fix the issue before outputting
4. Output ONLY the final README content (no checklist, no explanation)

Be specific about what each resource does and why it exists. Use code blocks for examples.
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
    except (boto3.exceptions.Boto3Error, KeyError, ValueError) as e:
        logging.error("Failed to generate README with Bedrock: %s", e)
        sys.exit(1)

def load_config_and_settings(args):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, 'config.json')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except IOError as e:
        logging.error("Failed to read config.json: %s", e)
        sys.exit(1)

    bedrock_model_id = args.bedrock_model_id or config.get('aws', {}).get('bedrock', {}).get('model_id', 'us.anthropic.claude-sonnet-4-20250514-v1:0')
    max_tokens_check = int(args.max_tokens_check or config.get('aws', {}).get('bedrock', {}).get('max_tokens_check', 200))
    max_tokens_generate = int(args.max_tokens_generate or config.get('aws', {}).get('bedrock', {}).get('max_tokens_generate', 16000))

    return script_dir, bedrock_model_id, max_tokens_check, max_tokens_generate

def handle_check_command(bedrock_client, source_code, readme_path, bedrock_config, *, output_file=None):
    current_readme = ""
    if os.path.exists(readme_path):
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                current_readme = f.read()
        except IOError as e:
            logging.error("Failed to read README: %s", e)
            sys.exit(1)

    logging.info("Checking if README should be updated via Bedrock...")
    readme_should_be_updated = check_readme_should_be_updated(
        bedrock_client, source_code, current_readme,
        bedrock_config['model_id'], bedrock_config['max_tokens']
    )

    if output_file:
        try:
            with open(output_file, 'a', encoding='utf-8') as f:
                f.write(f'readme_should_be_updated={str(readme_should_be_updated).lower()}\n')
            logging.info("Wrote readme_should_be_updated=%s to %s", readme_should_be_updated, output_file)
        except IOError as e:
            logging.error("Failed to write output file: %s", e)
            sys.exit(1)

def handle_update_command(bedrock_client, source_code, readme_path, bedrock_config):
    logging.info("Generating updated README via Bedrock...")
    new_readme = generate_readme(bedrock_client, source_code, bedrock_config['model_id'], bedrock_config['max_tokens'])

    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(new_readme)
        logging.info("Updated README written to %s", readme_path)
        print(f"README updated successfully: {readme_path}")
    except IOError as e:
        logging.error("Failed to write README: %s", e)
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

    if not args.check and not args.update:
        logging.error("Either --check or --update must be specified")
        sys.exit(1)

    if args.check and args.update:
        logging.error("Cannot specify both --check and --update")
        sys.exit(1)

    script_dir, bedrock_model_id, max_tokens_check, max_tokens_generate = load_config_and_settings(args)
    readme_path = os.path.join(script_dir, 'README.md')

    logging.info("Reading source files...")
    source_code = read_source_files()

    logging.info("Initializing Bedrock client...")
    try:
        bedrock_client = boto3.client('bedrock-runtime', region_name=args.aws_region)
    except boto3.exceptions.Boto3Error as e:
        logging.error("Failed to create Bedrock client: %s", e)
        sys.exit(1)

    if args.check:
        bedrock_config = {'model_id': bedrock_model_id, 'max_tokens': max_tokens_check}
        handle_check_command(bedrock_client, source_code, readme_path, bedrock_config, output_file=args.output_file)
    elif args.update:
        bedrock_config = {'model_id': bedrock_model_id, 'max_tokens': max_tokens_generate}
        handle_update_command(bedrock_client, source_code, readme_path, bedrock_config)

if __name__ == '__main__':
    main()
