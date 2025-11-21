from pathlib import Path


def test_terraform_tfvars_file_exists():
    tfvars_path = Path(__file__).parent.parent.parent / "src" / "foundation" / "terraform.tfvars"
    assert tfvars_path.exists()


def test_config_has_aws_region(config):
    assert 'aws_region' in config


def test_config_has_aws_account_id(config):
    assert 'aws_account_id' in config


def test_config_has_github_org(config):
    assert 'github_org' in config


def test_config_has_github_repo(config):
    assert 'github_repo' in config


def test_config_has_domain_name(config):
    assert 'domain_name' in config


def test_config_has_terraform_state_bucket_name(config):
    assert 'terraform_state_bucket_name' in config


def test_config_has_cloudtrail_name(config):
    assert 'cloudtrail_name' in config


def test_config_has_cloudtrail_bucket_name(config):
    assert 'cloudtrail_bucket_name' in config


def test_config_has_hosted_zone_id(config):
    assert 'hosted_zone_id' in config


def test_config_has_github_actions_role_name(config):
    assert 'github_actions_role_name' in config


def test_aws_region_is_valid(config):
    assert config['aws_region'] in ['us-east-1', 'us-west-2', 'eu-west-1']


def test_aws_account_id_is_numeric(config):
    assert config['aws_account_id'].isdigit()


def test_aws_account_id_has_12_digits(config):
    assert len(config['aws_account_id']) == 12


def test_github_org_is_not_empty(config):
    assert len(config['github_org']) > 0


def test_github_repo_is_not_empty(config):
    assert len(config['github_repo']) > 0


def test_domain_name_is_not_empty(config):
    assert len(config['domain_name']) > 0


def test_backend_tf_file_exists():
    backend_path = Path(__file__).parent.parent.parent / "src" / "foundation" / "backend.tf"
    assert backend_path.exists()


def test_providers_tf_file_exists():
    providers_path = Path(__file__).parent.parent.parent / "src" / "foundation" / "providers.tf"
    assert providers_path.exists()


def test_variables_tf_file_exists():
    variables_path = Path(__file__).parent.parent.parent / "src" / "foundation" / "variables.tf"
    assert variables_path.exists()


def test_outputs_tf_file_exists():
    outputs_path = Path(__file__).parent.parent.parent / "src" / "foundation" / "outputs.tf"
    assert outputs_path.exists()


def test_state_tf_file_exists():
    state_path = Path(__file__).parent.parent.parent / "src" / "foundation" / "state.tf"
    assert state_path.exists()


def test_cloudtrail_tf_file_exists():
    cloudtrail_path = Path(__file__).parent.parent.parent / "src" / "foundation" / "cloudtrail.tf"
    assert cloudtrail_path.exists()


def test_oidc_tf_file_exists():
    oidc_path = Path(__file__).parent.parent.parent / "src" / "foundation" / "oidc.tf"
    assert oidc_path.exists()


def test_domain_tf_file_exists():
    domain_path = Path(__file__).parent.parent.parent / "src" / "foundation" / "domain.tf"
    assert domain_path.exists()


def test_cloudtrail_module_exists():
    module_path = Path(__file__).parent.parent.parent / "src" / "foundation" / "modules" / "cloudtrail" / "main.tf"
    assert module_path.exists()


def test_github_oidc_module_exists():
    module_path = Path(__file__).parent.parent.parent / "src" / "foundation" / "modules" / "github-oidc" / "main.tf"
    assert module_path.exists()


def test_domain_module_exists():
    module_path = Path(__file__).parent.parent.parent / "src" / "foundation" / "modules" / "domain" / "main.tf"
    assert module_path.exists()
