from pathlib import Path
import pytest


CONFIG_MODULE_VALUES = {
    'admin_iam_user': 'jdrowne',
    'aws_account_id': '781581267945',
    'aws_region': 'us-east-1',
    'central_logs_bucket_name': '10ulabs-central-logs',
    'domain_name': '10ulabs.com',
    'github_org': '10U-Labs-LLC',
    'github_repo': '10ulabs.com',
    'resource_prefix': 'TenULabs',
    'terraform_state_bucket_name': '10ulabs-terraform-state',
}

LOCALS_DERIVED_VALUES = {
    'name_for_cloudtrail': f"{CONFIG_MODULE_VALUES['resource_prefix']}-cloudtrail",
    'name_for_cloudtrail_bucket': CONFIG_MODULE_VALUES['central_logs_bucket_name'],
    'name_for_cloudtrail_iam_role': f"{CONFIG_MODULE_VALUES['resource_prefix']}-cloudtrail-logs-role",
    'name_for_cloudtrail_log_group': f"/aws/cloudtrail/{CONFIG_MODULE_VALUES['resource_prefix']}",
    'name_for_github_actions_role': f"{CONFIG_MODULE_VALUES['resource_prefix']}-github-actions-role",
}


@pytest.fixture(name='bootstrap_dir')
def bootstrap_dir_fixture():
    return Path(__file__).parent.parent.parent / "src" / "bootstrap"


@pytest.fixture
def config(request):
    tfvars_path = request.getfixturevalue('bootstrap_dir') / "terraform.tfvars"
    config_dict = dict(CONFIG_MODULE_VALUES)
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
