"""Shared configuration fixture factories for pytest tests.

Provides factories to create config fixtures from terraform.tfvars files,
eliminating duplication across endpoint conftest.py files.
"""
import re
from pathlib import Path
from typing import Dict, Optional


def parse_tfvars_file(tfvars_path: Path) -> Dict[str, str]:
    """Parse a terraform.tfvars file and return key-value pairs.

    Args:
        tfvars_path: Path to the terraform.tfvars file

    Returns:
        Dictionary of key-value pairs from the file
    """
    config: Dict[str, str] = {}
    with open(tfvars_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"?([^"]+)"?', line)
                if match:
                    key, value = match.groups()
                    config[key] = value.strip('"')
    return config


def parse_locals_file(
    locals_path: Path,
    shared_config: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Parse a Terraform locals.tf file and return key-value pairs.

    Handles both quoted string values and module.common.* references.

    Args:
        locals_path: Path to the locals.tf file
        shared_config: Optional shared_config for resolving module.common.* refs

    Returns:
        Dictionary of parsed values
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
                    elif shared_config and 'module.common.' in value:
                        ref = value.replace('module.common.', '').strip()
                        config[key] = shared_config.get(ref, '')
    return config


def create_simple_config(tfvars_path: Path, shared_config: Dict[str, str]) -> Dict[str, str]:
    """Create a simple config dict from tfvars and shared config.

    This is the standard pattern used by diagnostics, health, simulation_soc,
    and similar endpoints that just need tfvars values plus aws_region and api_fqdn.

    Args:
        tfvars_path: Path to the terraform.tfvars file
        shared_config: The shared_config fixture value

    Returns:
        Merged configuration dictionary
    """
    result = parse_tfvars_file(tfvars_path)
    result['aws_region'] = shared_config['aws_region']
    result['api_fqdn'] = f"api.{shared_config.get('domain_name', '')}"
    return result


def create_website_config(
    locals_path: Path,
    shared_config: Dict[str, str],
    hosted_zone_id: str = ""
) -> Dict[str, str]:
    """Create a website config dict from locals.tf and shared config.

    Used by www_common tests to build configuration from Terraform locals.

    Args:
        locals_path: Path to the www/common/locals.tf file
        shared_config: The shared_config fixture value
        hosted_zone_id: Route53 hosted zone ID (optional, can be looked up separately)

    Returns:
        Website configuration dictionary
    """
    website_locals = parse_locals_file(locals_path, shared_config)
    domain_name = shared_config.get('domain_name', '')

    # Compute resource_prefix: shared prefix + "Website"
    # This handles the Terraform interpolation: "${module.common.resource_prefix}Website"
    base_prefix = shared_config.get('resource_prefix', '')
    resource_prefix = f"{base_prefix}Website" if base_prefix else ''

    return {
        'aws_region': shared_config['aws_region'],
        'aws_account_id': website_locals.get('aws_account_id', ''),
        'central_logs_bucket': shared_config.get('name_for_central_logs_bucket', ''),
        'website_fqdn': f"www.{domain_name}",
        'website_bucket_name': f"www-{domain_name.replace('.', '-')}",
        'apex_fqdn': domain_name,
        'github_org': shared_config.get('github_org', ''),
        'github_repo': (
            f"{shared_config.get('github_org', '')}/"
            f"{shared_config.get('name_for_github_repo', '')}"
        ),
        'resource_prefix': resource_prefix,
        'hosted_zone_id': hosted_zone_id,
    }
