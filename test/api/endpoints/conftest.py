"""Shared pytest fixtures and utilities for API endpoint tests."""
import io
import re
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List

import boto3

from repo_utils import extract_brace_block


def parse_terraform_archive_file_sources(tf_content: str) -> Dict[str, List[str]]:
    """Parse Terraform archive_file data sources and extract packaged filenames.

    Args:
        tf_content: Raw content of a Terraform .tf file.

    Returns:
        Dict mapping archive_file resource names to lists of filenames
        included in each archive via source blocks.
    """
    archives: Dict[str, List[str]] = {}

    # Find all archive_file data sources
    archive_start_pattern = r'data\s+"archive_file"\s+"([^"]+)"\s*\{'

    for match in re.finditer(archive_start_pattern, tf_content):
        archive_name = match.group(1)
        start_pos = match.end() - 1  # Position of opening brace

        archive_body = extract_brace_block(tf_content, start_pos)

        # Find source blocks and extract filenames using non-greedy matching
        source_filename_pattern = r'source\s*\{[\s\S]*?filename\s*=\s*"([^"]+)"[\s\S]*?\}'
        filenames = re.findall(source_filename_pattern, archive_body)
        archives[archive_name] = filenames

    return archives


def assert_archive_includes_file(
    tf_file_path: Path,
    archive_name: str,
    required_filename: str
) -> None:
    """Assert that a Terraform archive_file includes a specific file.

    Args:
        tf_file_path: Path to the Terraform file containing the archive_file.
        archive_name: Name of the archive_file data source.
        required_filename: Filename that must be included in the archive.

    Raises:
        AssertionError: If the archive doesn't include the required file.
    """
    with open(tf_file_path, encoding="utf-8") as f:
        content = f.read()

    archives = parse_terraform_archive_file_sources(content)

    assert archive_name in archives, (
        f"archive_file '{archive_name}' not found in {tf_file_path}"
    )

    assert required_filename in archives[archive_name], (
        f"'{required_filename}' not found in archive_file '{archive_name}'. "
        f"Found files: {archives[archive_name]}"
    )


def get_lambda_package_files(
    function_name: str,
    region: str = "us-east-1"
) -> List[str]:
    """Fetch a deployed Lambda's package and return list of files it contains.

    Args:
        function_name: Name of the Lambda function.
        region: AWS region where the Lambda is deployed.

    Returns:
        List of filenames in the Lambda deployment package.
    """
    lambda_client = boto3.client("lambda", region_name=region)
    response = lambda_client.get_function(FunctionName=function_name)
    code_location = response["Code"]["Location"]

    # Download the deployment package
    with urllib.request.urlopen(code_location) as resp:
        zip_bytes = resp.read()

    # Extract file list from zip
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        return zf.namelist()


def assert_lambda_package_includes_file(
    function_name: str,
    required_filename: str,
    region: str = "us-east-1"
) -> None:
    """Assert that a deployed Lambda package includes a specific file.

    Args:
        function_name: Name of the Lambda function.
        required_filename: Filename that must be in the deployment package.
        region: AWS region where the Lambda is deployed.

    Raises:
        AssertionError: If the Lambda package doesn't include the required file.
    """
    files = get_lambda_package_files(function_name, region)

    assert required_filename in files, (
        f"'{required_filename}' not found in Lambda '{function_name}' package. "
        f"Found files: {files}"
    )


def parse_tfvars(tfvars_path: Path) -> Dict[str, Any]:
    """Parse a Terraform tfvars file into a dict.

    Args:
        tfvars_path: Path to the tfvars file.

    Returns:
        Dict mapping variable names to values (strings or lists).
    """
    result: Dict[str, Any] = {}
    with open(tfvars_path, encoding="utf-8") as f:
        content = f.read()
    list_pattern = r'(\w+)\s*=\s*\[([^\]]*)\]'
    for match in re.finditer(list_pattern, content, re.DOTALL):
        key = match.group(1)
        values_str = match.group(2)
        values = [v.strip().strip('"') for v in values_str.split(',') if v.strip()]
        result[key] = values
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith("#") and '=' in line and '[' not in line:
            line_match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
            if line_match:
                key, value = line_match.groups()
                if key not in result:
                    result[key] = value.strip('"')
    return result


def parse_locals_file(locals_path: Path, shared: Dict[str, str]) -> Dict[str, str]:
    """Parse a Terraform locals file and resolve shared module references.

    Args:
        locals_path: Path to the locals.tf file.
        shared: Dict of shared module outputs for resolving references.

    Returns:
        Dict mapping local names to resolved values.
    """
    config: Dict[str, str] = {}
    with open(locals_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if '=' in line and not line.startswith('#') and not line.startswith('locals'):
                match = re.match(r'(\w+)\s*=\s*(.+)', line)
                if match:
                    key, value = match.groups()
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        config[key] = value[1:-1]
                    elif 'module.shared.' in value:
                        ref = value.replace('module.shared.', '').strip()
                        config[key] = shared.get(ref, '')
    return config
