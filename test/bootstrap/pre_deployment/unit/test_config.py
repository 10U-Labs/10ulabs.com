"""Unit tests for bootstrap configuration."""


def test_terraform_tfvars_file_exists(bootstrap_dir):
    """Test that terraform.tfvars file exists."""
    assert (bootstrap_dir / "terraform.tfvars").exists()


def test_config_has_name_for_cloudtrail(config):
    """Test that config has name_for_cloudtrail."""
    assert 'name_for_cloudtrail' in config


def test_config_has_name_for_cloudtrail_iam_role(config):
    """Test that config has name_for_cloudtrail_iam_role."""
    assert 'name_for_cloudtrail_iam_role' in config


def test_config_has_name_for_cloudtrail_log_group(config):
    """Test that config has name_for_cloudtrail_log_group."""
    assert 'name_for_cloudtrail_log_group' in config


def test_config_has_hosted_zone_id(config):
    """Test that config has hosted_zone_id."""
    assert 'hosted_zone_id' in config


def test_config_has_name_for_github_actions_role(config):
    """Test that config has name_for_github_actions_role."""
    assert 'name_for_github_actions_role' in config


def test_config_has_google_site_verification(config):
    """Test that config has google_site_verification."""
    assert 'google_site_verification' in config


def test_config_has_gmail_dns_ttl(config):
    """Test that config has gmail_dns_ttl."""
    assert 'gmail_dns_ttl' in config


def test_google_site_verification_is_not_empty(config):
    """Test that google_site_verification is not empty."""
    assert len(config['google_site_verification']) > 0


def test_gmail_dns_ttl_is_numeric(config):
    """Test that gmail_dns_ttl is numeric."""
    assert config['gmail_dns_ttl'].isdigit()


def test_hosted_zone_id_starts_with_z(config):
    """Test that hosted_zone_id starts with Z."""
    assert config['hosted_zone_id'].startswith('Z')
