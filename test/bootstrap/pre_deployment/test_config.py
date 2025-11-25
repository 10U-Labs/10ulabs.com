def test_terraform_tfvars_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "terraform.tfvars").exists()


def test_config_has_cloudtrail_name(config):
    assert 'cloudtrail_name' in config


def test_config_has_cloudtrail_bucket_name(config):
    assert 'cloudtrail_bucket_name' in config


def test_config_has_cloudtrail_iam_role_name(config):
    assert 'cloudtrail_iam_role_name' in config


def test_config_has_cloudtrail_log_group_name(config):
    assert 'cloudtrail_log_group_name' in config


def test_config_has_hosted_zone_id(config):
    assert 'hosted_zone_id' in config


def test_config_has_github_actions_role_name(config):
    assert 'github_actions_role_name' in config


def test_config_has_google_site_verification(config):
    assert 'google_site_verification' in config


def test_config_has_gmail_dns_ttl(config):
    assert 'gmail_dns_ttl' in config


def test_google_site_verification_is_not_empty(config):
    assert len(config['google_site_verification']) > 0


def test_gmail_dns_ttl_is_numeric(config):
    assert config['gmail_dns_ttl'].isdigit()


def test_hosted_zone_id_starts_with_z(config):
    assert config['hosted_zone_id'].startswith('Z')
