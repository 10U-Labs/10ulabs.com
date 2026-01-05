"""Unit tests for github_app.tf Terraform configuration."""
import hcl2
import pytest


def _load_github_app_tf(bootstrap_dir):
    """Load and parse github_app.tf."""
    with open(bootstrap_dir / "github_app.tf", encoding='utf-8') as f:
        return hcl2.load(f)


def _find_ssm_parameter(tf_config, param_name):
    """Find SSM parameter resource by name."""
    for resource in tf_config.get('resource', []):
        if 'aws_ssm_parameter' in resource:
            if param_name in resource['aws_ssm_parameter']:
                return resource['aws_ssm_parameter'][param_name]
    return None


class TestGitHubAppIdParameter:
    """Tests for github_app_id SSM parameter."""

    def test_resource_exists(self, bootstrap_dir):
        """Test that GitHub App ID SSM parameter resource exists."""
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_id')
        assert param is not None

    def test_type_is_string(self, bootstrap_dir):
        """Test that GitHub App ID parameter type is String."""
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_id')
        assert param['type'] == 'String'

    def test_has_name_tag(self, bootstrap_dir):
        """Test that GitHub App ID parameter has Name tag."""
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_id')
        assert param['tags']['Name'] == 'github-app-id'


class TestGitHubAppInstallationIdParameter:
    """Tests for github_app_installation_id SSM parameter."""

    def test_resource_exists(self, bootstrap_dir):
        """Test that GitHub App installation ID SSM parameter resource exists."""
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_installation_id')
        assert param is not None

    def test_type_is_string(self, bootstrap_dir):
        """Test that GitHub App installation ID parameter type is String."""
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_installation_id')
        assert param['type'] == 'String'

    def test_has_name_tag(self, bootstrap_dir):
        """Test that GitHub App installation ID parameter has Name tag."""
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_installation_id')
        assert param['tags']['Name'] == 'github-app-installation-id'


class TestGitHubAppPrivateKeyParameter:
    """Tests for github_app_private_key SSM parameter."""

    def test_resource_exists(self, bootstrap_dir):
        """Test that GitHub App private key SSM parameter resource exists."""
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_private_key')
        assert param is not None

    def test_type_is_secure_string(self, bootstrap_dir):
        """Test that GitHub App private key parameter type is SecureString."""
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_private_key')
        assert param['type'] == 'SecureString'

    def test_has_name_tag(self, bootstrap_dir):
        """Test that GitHub App private key parameter has Name tag."""
        tf_config = _load_github_app_tf(bootstrap_dir)
        param = _find_ssm_parameter(tf_config, 'github_app_private_key')
        assert param['tags']['Name'] == 'github-app-private-key'


@pytest.mark.parametrize("param_name", [
    "github_app_id",
    "github_app_installation_id",
    "github_app_private_key",
])
def test_all_github_app_parameters_exist(bootstrap_dir, param_name):
    """Verify all GitHub App SSM parameters are defined in terraform."""
    tf_config = _load_github_app_tf(bootstrap_dir)
    param = _find_ssm_parameter(tf_config, param_name)
    assert param is not None, f"SSM parameter '{param_name}' not found"
