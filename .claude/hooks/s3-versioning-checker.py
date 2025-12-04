#!/usr/bin/env python3
"""Check that S3 bucket versioning is disabled in IaC files."""
import json
import re
import sys


IAC_EXTENSIONS = ['.tf', '.json', '.yaml', '.yml', '.ts', '.py']


def is_iac_file(file_path):
    """Check if file is an infrastructure-as-code file."""
    result = any(file_path.endswith(ext) for ext in IAC_EXTENSIONS)
    return result


def check_terraform(content):
    """Check Terraform for S3 versioning enabled."""
    versioning_pattern = r'versioning\s*\{[^}]*enabled\s*=\s*true'
    if re.search(versioning_pattern, content, re.IGNORECASE | re.DOTALL):
        return ["Terraform: S3 bucket versioning enabled (versioning { enabled = true })"]
    return []


def check_cloudformation(content):
    """Check CloudFormation for S3 versioning enabled."""
    violations = []
    versioning_pattern = r'VersioningConfiguration:\s*\n\s*Status:\s*Enabled'
    if re.search(versioning_pattern, content, re.IGNORECASE):
        violations.append("CloudFormation: S3 bucket versioning enabled")
    return violations


def check_cdk_typescript(content):
    """Check CDK TypeScript for S3 versioning enabled."""
    violations = []
    patterns = [
        r'versioned:\s*true',
        r'versioning:\s*true',
        r'BucketVersioning\.ENABLED',
    ]
    for pattern in patterns:
        if re.search(pattern, content):
            violations.append(f"CDK: S3 bucket versioning enabled ({pattern})")
    return violations


def check_cdk_python(content):
    """Check CDK Python for S3 versioning enabled."""
    violations = []
    patterns = [
        r'versioned\s*=\s*True',
        r'versioning\s*=\s*True',
        r'BucketVersioning\.ENABLED',
    ]
    for pattern in patterns:
        if re.search(pattern, content):
            violations.append(f"CDK: S3 bucket versioning enabled ({pattern})")
    return violations


def check_content(content, file_path):
    """Check content for S3 versioning issues."""
    violations = []

    if not is_iac_file(file_path):
        return violations

    if 's3' not in content.lower() and 'bucket' not in content.lower():
        return violations

    if file_path.endswith('.tf'):
        violations.extend(check_terraform(content))
    elif file_path.endswith(('.yaml', '.yml', '.json')):
        violations.extend(check_cloudformation(content))
    elif file_path.endswith('.ts'):
        violations.extend(check_cdk_typescript(content))
    elif file_path.endswith('.py'):
        violations.extend(check_cdk_python(content))

    return violations


def main():
    input_data = sys.stdin.read()
    try:
        data = json.loads(input_data)
        tool_input = data.get('tool_input', {})
    except json.JSONDecodeError:
        sys.exit(0)

    file_path = tool_input.get('file_path', '')
    content = tool_input.get('content', '')
    new_string = tool_input.get('new_string', '')

    text_to_check = content or new_string
    if not text_to_check or not file_path:
        sys.exit(0)

    violations = check_content(text_to_check, file_path)

    if violations:
        print("BLOCKED: S3 bucket versioning must be disabled:")
        for violation in violations:
            print(f"  - {violation}")
        sys.exit(2)

    sys.exit(0)


if __name__ == '__main__':
    main()
