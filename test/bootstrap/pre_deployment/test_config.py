def test_terraform_tfvars_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "terraform.tfvars").exists()


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


def test_config_has_google_site_verification(config):
    assert 'google_site_verification' in config


def test_config_has_gmail_dns_ttl(config):
    assert 'gmail_dns_ttl' in config


def test_google_site_verification_is_not_empty(config):
    assert len(config['google_site_verification']) > 0


def test_gmail_dns_ttl_is_numeric(config):
    assert config['gmail_dns_ttl'].isdigit()
