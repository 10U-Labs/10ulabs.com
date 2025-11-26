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
    with open(LOCALS_TF_PATH, encoding='utf-8') as f:
        content = f.read()
    pattern = rf'{local_name}\s*=\s*"\${{local\.resource_prefix}}([^"]+)"'
    match = re.search(pattern, content)
    return match.group(1) if match else ''


LOCALS_DERIVED_VALUES = {
    'name_for_cloudtrail': f"{SHARED_MODULE_VALUES['resource_prefix']}-cloudtrail",
    'name_for_cloudtrail_bucket': SHARED_MODULE_VALUES['name_for_central_logs_bucket'],
    'name_for_cloudtrail_iam_role': f"{SHARED_MODULE_VALUES['resource_prefix']}{_extract_role_suffix('name_for_cloudtrail_iam_role')}",
    'name_for_cloudtrail_log_group': f"/aws/cloudtrail/{SHARED_MODULE_VALUES['resource_prefix']}",
    'name_for_github_actions_role': f"{SHARED_MODULE_VALUES['resource_prefix']}{_extract_role_suffix('name_for_github_actions_role')}",
}


@pytest.fixture(name='bootstrap_dir')
def bootstrap_dir_fixture():
    return BOOTSTRAP_DIR


@pytest.fixture
def config(request):
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
