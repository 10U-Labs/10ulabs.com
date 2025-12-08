"""Pytest fixtures for bootstrap tests."""
from pathlib import Path
import re
import pytest


BOOTSTRAP_DIR = Path(__file__).parent.parent.parent / "src" / "bootstrap"
SHARED_MODULE_DIR = Path(__file__).parent.parent.parent / "lib" / "terraform" / "modules" / "shared"
LOCALS_TF_PATH = BOOTSTRAP_DIR / "locals.tf"


def _parse_shared_module_locals() -> dict:
    """Parse locals from the shared Terraform module."""
    locals_path = SHARED_MODULE_DIR / "locals.tf"
    with open(locals_path, encoding='utf-8') as f:
        content = f.read()

    values = {}
    # Match simple string assignments: key = "value"
    for match in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', content):
        values[match.group(1)] = match.group(2)
    return values


def _parse_shared_module_outputs(locals_dict: dict) -> dict:
    """Parse outputs from the shared Terraform module, resolving local references."""
    outputs_path = SHARED_MODULE_DIR / "outputs.tf"
    with open(outputs_path, encoding='utf-8') as f:
        content = f.read()

    values = {}
    # Match output blocks: output "name" { value = "string" } or { value = local.X }
    for match in re.finditer(
        r'output\s+"(\w+)"\s*\{\s*value\s*=\s*(?:"([^"]*)"|local\.(\w+))\s*\}',
        content
    ):
        output_name = match.group(1)
        if match.group(2) is not None:
            values[output_name] = match.group(2)
        elif match.group(3):
            local_ref = match.group(3)
            if local_ref in locals_dict:
                values[output_name] = locals_dict[local_ref]
    return values


def _get_shared_module_values() -> dict:
    """Get all values from the shared Terraform module."""
    locals_dict = _parse_shared_module_locals()
    outputs_dict = _parse_shared_module_outputs(locals_dict)
    return outputs_dict


SHARED_MODULE_VALUES = _get_shared_module_values()


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
    'ssm_parameter_name_for_github_pat': SHARED_MODULE_VALUES.get('ssm_github_pat_name', ''),
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
