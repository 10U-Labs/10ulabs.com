#!/usr/bin/env python3
import argparse
import json
import logging
import os
import random
import sys
import time
import glob
import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stderr
)

def split_text_by_words(text: str, max_length: int = 1000) -> list:
    if len(text) <= max_length:
        return [text]

    chunks = []
    current_chunk = ""

    words = text.split()
    for word in words:
        if len(current_chunk) + len(word) + 1 <= max_length:
            if current_chunk:
                current_chunk += " " + word
            else:
                current_chunk = word
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = word

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def call_bedrock_with_retry(bedrock_client, bedrock_config: dict, messages: list, max_retries: int = 5) -> dict:
    initial_jitter = random.uniform(5, 30)
    logging.info("Waiting %.2fs before Bedrock call to avoid thundering herd", initial_jitter)
    time.sleep(initial_jitter)

    for attempt in range(1, max_retries + 1):
        try:
            response = bedrock_client.converse(
                modelId=bedrock_config['model_id'],
                messages=messages,
                inferenceConfig={'maxTokens': bedrock_config['max_tokens']}
            )
            logging.info("Bedrock call succeeded on attempt %d", attempt)
            return response
        except ClientError as e:
            if e.response['Error']['Code'] == 'ThrottlingException':
                if attempt == max_retries:
                    logging.error("Bedrock throttled after %d attempts", max_retries)
                    raise
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logging.warning("Bedrock throttled, retrying in %.2fs (attempt %d/%d)",
                               wait_time, attempt, max_retries)
                time.sleep(wait_time)
            else:
                raise

    raise RuntimeError("Bedrock retry loop exited unexpectedly")

def find_all_project_files(project_dir: str) -> list:
    all_files = []

    patterns = [
        os.path.join(project_dir, '*.py'),
        os.path.join(project_dir, '*.json'),
        os.path.join(project_dir, '*.txt'),
        os.path.join(project_dir, '*.yaml'),
        os.path.join(project_dir, '*.yml'),
        os.path.join(project_dir, 'lambda', '*.py'),
        os.path.join(project_dir, 'lambda', '*', '*.py'),
    ]

    for pattern in patterns:
        all_files.extend(glob.glob(pattern))

    excluded_names = ['readme.py', 'conftest.py', 'test_', 'README.md']
    all_files = [
        f for f in all_files
        if not any(excluded in os.path.basename(f) for excluded in excluded_names)
    ]

    return sorted(all_files)

def read_all_project_files(project_dir: str) -> str:
    all_file_paths = find_all_project_files(project_dir)

    repo_root = project_dir
    while repo_root and repo_root != '/':
        if os.path.exists(os.path.join(repo_root, 'scripts', 'readme.py')):
            break
        repo_root = os.path.dirname(repo_root)

    if os.path.exists(os.path.join(repo_root, 'scripts', 'readme.py')):
        all_file_paths.append(os.path.join(repo_root, 'scripts', 'readme.py'))

    if not all_file_paths:
        logging.warning("No files found in %s", project_dir)
        return ""

    all_files = {}
    for full_path in all_file_paths:
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                if 'scripts/readme.py' in full_path:
                    rel_path = 'scripts/readme.py'
                else:
                    rel_path = os.path.relpath(full_path, project_dir)
                all_files[rel_path] = f.read()
        except IOError as e:
            logging.error("Failed to read %s: %s", full_path, e)
            sys.exit(1)

    combined = ""
    for file_path, content in all_files.items():
        combined += f"\n\n{'='*60}\nFile: {file_path}\n{'='*60}\n{content}"

    return combined

def check_readme_should_be_updated(bedrock_client, project_files: str, current_readme: str, bedrock_config: dict) -> bool:
    if not current_readme or not current_readme.strip():
        logging.info("README is empty or missing - should be updated")
        return True

    prompt = f"""You are a technical documentation expert. Your task is to determine if a README file is current and accurate for the given infrastructure code.

<project_files>
{project_files}
</project_files>

<current_readme>
{current_readme}
</current_readme>

Check if the README has ANY issues, including but not limited to:
1. Title doesn't match actual infrastructure name
2. Inconsistent or outdated terminology throughout the document
3. Inaccurately describes the infrastructure components
4. Missing or incorrect documentation of authentication flow
5. Incorrect usage instructions or command examples
6. Missing key resources created
7. Outdated command examples or file paths
8. Missing or incorrect prerequisites
9. Contains a "License" section (MAJOR ERROR - repository has LICENSE.md, README must not duplicate licensing)
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
        messages = [{
            'role': 'user',
            'content': [{'text': prompt}]
        }]
        response = call_bedrock_with_retry(bedrock_client, bedrock_config, messages)

        answer_text = response['output']['message']['content'][0]['text'].strip()
        try:
            result = json.loads(answer_text)
            should_be_updated = bool(result.get('readme_should_be_updated', False))
            reasoning_chunks = split_text_by_words(result.get('reasoning', 'No reasoning provided'), max_length=1000)
            if len(reasoning_chunks) == 1:
                logging.info("Bedrock reasoning: %s", reasoning_chunks[0])
            else:
                for i, chunk in enumerate(reasoning_chunks, 1):
                    logging.info("Bedrock reasoning (part %d/%d): %s", i, len(reasoning_chunks), chunk)
            logging.info("Bedrock assessment: README should %s", 'be updated' if should_be_updated else 'not be updated')
            return should_be_updated
        except json.JSONDecodeError as e:
            logging.warning("Failed to parse JSON response from Bedrock: %s", e)
            logging.warning("Raw response: %s", answer_text)
            should_be_updated = answer_text.lower().startswith('true')
            logging.info("Bedrock assessment: README should %s", 'be updated (fallback)' if should_be_updated else 'not be updated (fallback)')
            return should_be_updated
    except (KeyError, IndexError, TypeError) as e:
        logging.error("Failed to check README with Bedrock: %s", e)
        sys.exit(1)

def generate_readme(bedrock_client, project_files: str, bedrock_config: dict) -> str:
    prompt = f"""You are a technical documentation expert. Generate a comprehensive README.md file for the following infrastructure code.

<project_files>
{project_files}
</project_files>

Create a professional README that includes:
1. Title and overview of what this infrastructure does
2. Purpose and key features
3. Resources created (analyze the code to identify all AWS resources)
4. Prerequisites and requirements:
   - CRITICAL: Use ONLY dependencies found in requirements.txt file from project_files - DO NOT invent or assume additional dependencies
   - If AWS CLI is NOT in requirements.txt, DO NOT list it as a requirement
   - AWS CDK uses boto3 (Python SDK), NOT the AWS CLI tool
   - List Python packages from requirements.txt
   - List system dependencies needed to run those packages (e.g., Node.js for AWS CDK)
5. Configuration details (analyze config.json and cdk.json files from project_files)
6. Usage instructions:
   - Installation steps
   - Running the infrastructure (CDK deploy, scripts, etc.)
   - How to use the deployed resources
7. Architecture overview:
   - How the components interact
   - Authentication and authorization flows
   - Data flows and integrations
8. Security considerations
9. Troubleshooting tips

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

   FACTUAL ACCURACY (verify against project_files):
   - [ ] Prerequisites list ONLY dependencies from requirements.txt in project_files - NO invented dependencies
   - [ ] AWS CLI is NOT listed as requirement (AWS CDK uses boto3, not AWS CLI)
   - [ ] Python packages match requirements.txt exactly
   - [ ] System dependencies (Node.js, Git) are accurate for the packages used
   - [ ] Resource descriptions match implementation in Python files
   - [ ] Configuration examples match actual config.json and cdk.json files
   - [ ] Usage instructions are accurate and complete

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
        messages = [{
            'role': 'user',
            'content': [{'text': prompt}]
        }]
        response = call_bedrock_with_retry(bedrock_client, bedrock_config, messages)

        readme_content = response['output']['message']['content'][0]['text']

        if not readme_content.endswith('\n'):
            readme_content += '\n'
            logging.info("Added missing trailing newline to README")

        logging.info("Successfully generated README with Bedrock")
        return readme_content
    except (KeyError, IndexError, TypeError) as e:
        logging.error("Failed to generate README with Bedrock: %s", e)
        sys.exit(1)

def load_config(project_dir: str):
    config_path = os.path.join(project_dir, 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except IOError as e:
        logging.error("Failed to read config.json: %s", e)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='Generate or check README for infrastructure projects')
    parser.add_argument('--check', action='store_true', help='Check if README is current')
    parser.add_argument('--update', action='store_true', help='Update README')
    parser.add_argument('--project-dir', required=True, help='Project directory path')
    parser.add_argument('--aws-region', required=True, help='AWS region')
    parser.add_argument('--output-file', help='Output file for check result (for GitHub Actions)')
    parser.add_argument('--bedrock-model-id', help='Bedrock model ID to use')
    parser.add_argument('--max-tokens-check', type=int, help='Max tokens for README check')
    parser.add_argument('--max-tokens-generate', type=int, help='Max tokens for README generation')
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        logging.error("Project directory does not exist: %s", project_dir)
        sys.exit(1)

    config = load_config(project_dir)

    if not args.check and not args.update:
        logging.error("Must specify either --check or --update")
        sys.exit(1)

    bedrock_client = boto3.client('bedrock-runtime', region_name=args.aws_region)
    project_files = read_all_project_files(project_dir)

    if args.check:
        try:
            with open(os.path.join(project_dir, 'README.md'), 'r', encoding='utf-8') as f:
                current_readme = f.read()
        except FileNotFoundError:
            current_readme = ""

        bedrock_config = {
            'model_id': args.bedrock_model_id or config.get('aws', {}).get('bedrock', {}).get('model_id', 'us.anthropic.claude-sonnet-4-20250514-v1:0'),
            'max_tokens': int(args.max_tokens_check or config.get('aws', {}).get('bedrock', {}).get('max_tokens_check', 200))
        }
        should_be_updated = check_readme_should_be_updated(bedrock_client, project_files, current_readme, bedrock_config)

        if args.output_file:
            with open(args.output_file, 'a', encoding='utf-8') as f:
                f.write(f"readme_should_be_updated={'true' if should_be_updated else 'false'}\n")

        sys.exit(0)

    elif args.update:
        bedrock_config = {
            'model_id': args.bedrock_model_id or config.get('aws', {}).get('bedrock', {}).get('model_id', 'us.anthropic.claude-sonnet-4-20250514-v1:0'),
            'max_tokens': int(args.max_tokens_generate or config.get('aws', {}).get('bedrock', {}).get('max_tokens_generate', 16000))
        }
        new_readme = generate_readme(bedrock_client, project_files, bedrock_config)

        with open(os.path.join(project_dir, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(new_readme)

        logging.info("README updated at %s", os.path.join(project_dir, 'README.md'))
        sys.exit(0)

if __name__ == '__main__':
    main()
