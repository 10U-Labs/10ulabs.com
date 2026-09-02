from pathlib import Path
from typing import Any, Dict
def test_terraform_tfvars_file_exists(bootstrap_dir: Path) -> None:
    assert (bootstrap_dir / "terraform.tfvars").exists()


def test_config_has_name_for_cloudtrail(config: Dict[str, Any]) -> None:
    assert 'name_for_cloudtrail' in config


def test_config_has_name_for_cloudtrail_iam_role(config: Dict[str, Any]) -> None:
    assert 'name_for_cloudtrail_iam_role' in config


def test_config_has_name_for_cloudtrail_log_group(config: Dict[str, Any]) -> None:
    assert 'name_for_cloudtrail_log_group' in config


def test_config_has_hosted_zone_id(config: Dict[str, Any]) -> None:
    assert 'hosted_zone_id' in config


def test_config_has_name_for_github_actions_role(config: Dict[str, Any]) -> None:
    assert 'name_for_github_actions_role' in config


def test_config_has_google_site_verification(config: Dict[str, Any]) -> None:
    assert 'google_site_verification' in config


def test_config_has_gmail_dns_ttl(config: Dict[str, Any]) -> None:
    assert 'gmail_dns_ttl' in config


def test_google_site_verification_is_not_empty(config: Dict[str, Any]) -> None:
    assert len(config['google_site_verification']) > 0


def test_gmail_dns_ttl_is_numeric(config: Dict[str, Any]) -> None:
    assert config['gmail_dns_ttl'].isdigit()


def test_hosted_zone_id_starts_with_z(config: Dict[str, Any]) -> None:
    assert config['hosted_zone_id'].startswith('Z')
