import re
from pathlib import Path
from typing import Dict, Optional


def parse_tfvars_file(tfvars_path: Path) -> Dict[str, str]:
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
    result = parse_tfvars_file(tfvars_path)
    result['aws_region'] = shared_config['aws_region']
    result['api_fqdn'] = f"api.{shared_config.get('domain_name', '')}"
    return result


def create_website_config(
    locals_path: Path,
    shared_config: Dict[str, str],
    hosted_zone_id: str = ""
) -> Dict[str, str]:
    website_locals = parse_locals_file(locals_path, shared_config)
    domain_name = shared_config.get('domain_name', '')

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
