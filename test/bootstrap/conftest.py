"""Pytest fixtures for bootstrap tests."""
from pathlib import Path
import re
import pytest


BOOTSTRAP_DIR = Path(__file__).parent.parent.parent / "src" / "bootstrap"
LOCALS_TF_PATH = BOOTSTRAP_DIR / "locals.tf"

SHARED_MODULE_VALUES = {
    'admin_iam_user': 'jdrowne',
    'aws_account_id': '781581267945',
    'aws_region': 'us-east-1',
    'domain_name': '10ulabs.com',
    'github_org': '10U-Labs-LLC',
    'name_for_central_logs_bucket': '10ulabs-central-logs',
    'name_for_github_repo': '10ulabs.com',
    'name_for_terraform_state_bucket': '10ulabs-terraform-state',
    'resource_prefix': 'TenULabs',
}


def _extract_role_suffix(local_name: str) -> str:
    """Extract role name suffix from locals.tf file."""
    with open(LOCALS_TF_PATH, encoding='utf-8') as f:
        content = f.read()
    pattern = rf'{local_name}\s*=\s*"\${{local\.resource_prefix}}([^"]+)"'
    match = re.search(pattern, content)
    return match.group(1) if match else ''


_PREFIX = SHARED_MODULE_VALUES['resource_prefix']
_LOGS = SHARED_MODULE_VALUES['name_for_central_logs_bucket']
_CT_SUFFIX = _extract_role_suffix('name_for_cloudtrail_iam_role')
_GH_SUFFIX = _extract_role_suffix('name_for_github_actions_role')

LOCALS_DERIVED_VALUES = {
    'name_for_cloudtrail': f"{_PREFIX}-cloudtrail",
    'name_for_cloudtrail_bucket': _LOGS,
    'name_for_cloudtrail_iam_role': f"{_PREFIX}{_CT_SUFFIX}",
    'name_for_cloudtrail_log_group': f"/aws/cloudtrail/{_PREFIX}",
    'name_for_github_actions_role': f"{_PREFIX}{_GH_SUFFIX}",
}


@pytest.fixture(name='bootstrap_dir')
def bootstrap_dir_fixture():
    """Provide path to bootstrap directory."""
    return BOOTSTRAP_DIR


@pytest.fixture
def config(request):
    """Provide combined configuration from shared module and tfvars."""
    tfvars_path = request.getfixturevalue('bootstrap_dir') / "terraform.tfvars"
    config_dict = dict(SHARED_MODULE_VALUES)
    config_dict.update(LOCALS_DERIVED_VALUES)
    with open(tfvars_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"')
                config_dict[key] = value
    return config_dict
