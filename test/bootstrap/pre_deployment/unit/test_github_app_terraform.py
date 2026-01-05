"""Unit tests for github_app.tf Terraform configuration."""
import hcl2


def test_github_app_id_parameter_resource_exists(bootstrap_dir):
    """Test that GitHub App ID SSM parameter resource exists."""
    with open(bootstrap_dir / "github_app.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    assert 'resource' in tf_config
    param_found = False
    for resource in tf_config['resource']:
        if 'aws_ssm_parameter' in resource:
            if 'github_app_id' in resource['aws_ssm_parameter']:
                param_found = True
                break
    assert param_found


def test_github_app_installation_id_parameter_resource_exists(bootstrap_dir):
    """Test that GitHub App installation ID SSM parameter resource exists."""
    with open(bootstrap_dir / "github_app.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    param_found = False
    for resource in tf_config['resource']:
        if 'aws_ssm_parameter' in resource:
            if 'github_app_installation_id' in resource['aws_ssm_parameter']:
                param_found = True
                break
    assert param_found


def test_github_app_private_key_parameter_resource_exists(bootstrap_dir):
    """Test that GitHub App private key SSM parameter resource exists."""
    with open(bootstrap_dir / "github_app.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    param_found = False
    for resource in tf_config['resource']:
        if 'aws_ssm_parameter' in resource:
            if 'github_app_private_key' in resource['aws_ssm_parameter']:
                param_found = True
                break
    assert param_found


def test_github_app_id_parameter_type_is_string(bootstrap_dir):
    """Test that GitHub App ID parameter type is String."""
    with open(bootstrap_dir / "github_app.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    for resource in tf_config['resource']:
        if 'aws_ssm_parameter' in resource:
            param = resource['aws_ssm_parameter'].get('github_app_id')
            if param:
                assert param['type'] == 'String'
                return
    assert False, "github_app_id parameter not found"


def test_github_app_installation_id_parameter_type_is_string(bootstrap_dir):
    """Test that GitHub App installation ID parameter type is String."""
    with open(bootstrap_dir / "github_app.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    for resource in tf_config['resource']:
        if 'aws_ssm_parameter' in resource:
            param = resource['aws_ssm_parameter'].get('github_app_installation_id')
            if param:
                assert param['type'] == 'String'
                return
    assert False, "github_app_installation_id parameter not found"


def test_github_app_private_key_parameter_type_is_secure_string(bootstrap_dir):
    """Test that GitHub App private key parameter type is SecureString."""
    with open(bootstrap_dir / "github_app.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    for resource in tf_config['resource']:
        if 'aws_ssm_parameter' in resource:
            param = resource['aws_ssm_parameter'].get('github_app_private_key')
            if param:
                assert param['type'] == 'SecureString'
                return
    assert False, "github_app_private_key parameter not found"


def test_github_app_id_parameter_has_name_tag(bootstrap_dir):
    """Test that GitHub App ID parameter has Name tag."""
    with open(bootstrap_dir / "github_app.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    for resource in tf_config['resource']:
        if 'aws_ssm_parameter' in resource:
            param = resource['aws_ssm_parameter'].get('github_app_id')
            if param:
                assert 'tags' in param
                assert param['tags']['Name'] == 'github-app-id'
                return
    assert False, "github_app_id parameter not found"


def test_github_app_installation_id_parameter_has_name_tag(bootstrap_dir):
    """Test that GitHub App installation ID parameter has Name tag."""
    with open(bootstrap_dir / "github_app.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    for resource in tf_config['resource']:
        if 'aws_ssm_parameter' in resource:
            param = resource['aws_ssm_parameter'].get('github_app_installation_id')
            if param:
                assert 'tags' in param
                assert param['tags']['Name'] == 'github-app-installation-id'
                return
    assert False, "github_app_installation_id parameter not found"


def test_github_app_private_key_parameter_has_name_tag(bootstrap_dir):
    """Test that GitHub App private key parameter has Name tag."""
    with open(bootstrap_dir / "github_app.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    for resource in tf_config['resource']:
        if 'aws_ssm_parameter' in resource:
            param = resource['aws_ssm_parameter'].get('github_app_private_key')
            if param:
                assert 'tags' in param
                assert param['tags']['Name'] == 'github-app-private-key'
                return
    assert False, "github_app_private_key parameter not found"
