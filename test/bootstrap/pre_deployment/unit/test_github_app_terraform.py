from pathlib import Path
from typing import Any, Dict

import hcl2
import pytest


def _load_github_app_tf(bootstrap_dir: Path, v7_compatible: Any) -> Dict[str, Any]:
    with open(bootstrap_dir / "github_app.tf", encoding='utf-8') as f:
        return hcl2.load(f, serialization_options=v7_compatible)


def _find_ssm_parameter(tf_config: Any, param_name: str) -> Any:
    for resource in tf_config.get('resource', []):
        if 'aws_ssm_parameter' in resource:
            if param_name in resource['aws_ssm_parameter']:
                return resource['aws_ssm_parameter'][param_name]
    return None


@pytest.mark.parametrize("param_name", [
    "github_app_id",
    "github_app_installation_id",
    "github_app_private_key",
])
def test_all_github_app_parameters_exist(
    bootstrap_dir: Path,
    param_name: str,
    v7_compatible: Any
) -> None:
    tf_config = _load_github_app_tf(bootstrap_dir, v7_compatible)
    param = _find_ssm_parameter(tf_config, param_name)
    assert param is not None, f"SSM parameter '{param_name}' not found"


@pytest.mark.parametrize("param_name, expected_type", [
    ("github_app_id", "String"),
    ("github_app_installation_id", "String"),
    ("github_app_private_key", "SecureString"),
])
def test_every_github_app_parameter_declares_its_type(
    bootstrap_dir: Path,
    param_name: str,
    expected_type: str,
    v7_compatible: Any
) -> None:
    tf_config = _load_github_app_tf(bootstrap_dir, v7_compatible)
    param = _find_ssm_parameter(tf_config, param_name)
    assert param['type'] == expected_type


@pytest.mark.parametrize("param_name, expected_tag", [
    ("github_app_id", "github-app-id"),
    ("github_app_installation_id", "github-app-installation-id"),
    ("github_app_private_key", "github-app-private-key"),
])
def test_every_github_app_parameter_carries_its_name_tag(
    bootstrap_dir: Path,
    param_name: str,
    expected_tag: str,
    v7_compatible: Any
) -> None:
    tf_config = _load_github_app_tf(bootstrap_dir, v7_compatible)
    param = _find_ssm_parameter(tf_config, param_name)
    assert param['tags']['Name'] == expected_tag
