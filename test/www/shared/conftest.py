import re
from pathlib import Path
from typing import Dict
import pytest

REPO_ROOT = Path(__file__).parent.parent.parent.parent


def parse_shared_module_outputs() -> Dict[str, str]:
    outputs_path = REPO_ROOT / "lib" / "terraform" / "outputs.tf"
    config = {}
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()
    pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*"([^"]+)"'
    matches = re.findall(pattern, content)
    for key, value in matches:
        config[key] = value
    return config


def parse_website_locals() -> Dict[str, str]:
    locals_path = REPO_ROOT / "src" / "www" / "home_page" / "locals.tf"
    shared = parse_shared_module_outputs()
    config = {}
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
    config['www_fqdn'] = f"www.{shared.get('domain_name', '')}"
    config['apex_fqdn'] = shared.get('domain_name', '')
    config['github_repo_full'] = f"{shared.get('github_org', '')}/{shared.get('name_for_github_repo', '')}"
    return config


@pytest.fixture(name="config", scope="module")
def config_fixture() -> Dict[str, str]:
    shared = parse_shared_module_outputs()
    website_locals = parse_website_locals()
    result = {}
    result['aws_region'] = website_locals.get('aws_region', '')
    result['aws_account_id'] = website_locals.get('aws_account_id', '')
    result['central_logs_bucket'] = shared.get('name_for_central_logs_bucket', '')
    result['website_fqdn'] = website_locals.get('www_fqdn', '')
    result['apex_fqdn'] = website_locals.get('apex_fqdn', '')
    result['github_org'] = shared.get('github_org', '')
    result['github_repo'] = website_locals.get('github_repo_full', '')
    result['resource_prefix'] = website_locals.get('resource_prefix', '')
    return result


@pytest.fixture(name="website_src_path")
def fixture_website_src_path():
    return REPO_ROOT / "src" / "www" / "home_page"


@pytest.fixture(name="cloudfront_s3_tf_content")
def fixture_cloudfront_s3_tf_content(website_src_path):
    with open(website_src_path / "cloudfront_s3.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(name="certificate_dns_tf_content")
def fixture_certificate_dns_tf_content(website_src_path):
    with open(website_src_path / "certificate_dns.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(name="contact_form_tf_content")
def fixture_contact_form_tf_content(website_src_path):
    with open(website_src_path / "contact_form.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(name="contact_lambda_content")
def fixture_contact_lambda_content(website_src_path):
    with open(website_src_path / "lambdas" / "contact.py", encoding="utf-8") as f:
        return f.read()
