from test.bootstrap.pre_deployment.unit.conftest import V7_COMPATIBLE

import hcl2
import pytest


def _load_github_app_tf(bootstrap_dir):
    with open(bootstrap_dir / "github_app.tf", encoding='utf-8') as f:
        return hcl2.load(f, serialization_options=V7_COMPATIBLE)


def _find_ssm_parameter(tf_config, param_name):
    for resource in tf_config.get('resource', []):
        if 'aws_ssm_parameter' in resource:
            if param_name in resource['aws_ssm_parameter']:
                return resource['aws_ssm_parameter'][param_name]
    return None


class TestGitHubAppIdParameter:
    def test_resource_exists(self, bootstrap_dir):
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_id')
        assert param is not None

    def test_type_is_string(self, bootstrap_dir):
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_id')
        assert param['type'] == 'String'

    def test_has_name_tag(self, bootstrap_dir):
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_id')
        assert param['tags']['Name'] == 'github-app-id'


class TestGitHubAppInstallationIdParameter:
    def test_resource_exists(self, bootstrap_dir):
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_installation_id')
        assert param is not None

    def test_type_is_string(self, bootstrap_dir):
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_installation_id')
        assert param['type'] == 'String'

    def test_has_name_tag(self, bootstrap_dir):
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_installation_id')
        assert param['tags']['Name'] == 'github-app-installation-id'


class TestGitHubAppPrivateKeyParameter:
    def test_resource_exists(self, bootstrap_dir):
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_private_key')
        assert param is not None

    def test_type_is_secure_string(self, bootstrap_dir):
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_private_key')
        assert param['type'] == 'SecureString'

    def test_has_name_tag(self, bootstrap_dir):
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_private_key')
        assert param['tags']['Name'] == 'github-app-private-key'


@pytest.mark.parametrize("param_name", [
    "github_app_id",
    "github_app_installation_id",
    "github_app_private_key",
])
def test_all_github_app_parameters_exist(bootstrap_dir, param_name):
    tf_config = _load_github_app_tf(bootstrap_dir)
    param = _find_ssm_parameter(tf_config, param_name)
    assert param is not None, f"SSM parameter '{param_name}' not found"
