"""Tests for certificate_dns.tf Terraform configuration."""

from pathlib import Path


def _get_terraform_path() -> Path:
    """Get the path to certificate_dns.tf file."""
    base = Path(__file__).parent.parent.parent.parent.parent.parent.parent
    return base / "src" / "api" / "shared" / "routing" / "certificate_dns.tf"


def test_certificate_dns_terraform_file_exists():
    """Verify that certificate_dns.tf file exists."""
    cert_file = _get_terraform_path()
    assert cert_file.exists()


def test_route53_zone_data_source_exists():
    """Verify that Route53 zone data source exists."""
    cert_file = _get_terraform_path()
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "aws_route53_zone" "parent"' in content


def test_acm_certificate_resource_exists():
    """Verify that ACM certificate resource exists."""
    cert_file = _get_terraform_path()
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_acm_certificate" "api"' in content


def test_acm_certificate_has_validation_method():
    """Verify that ACM certificate has validation method."""
    cert_file = _get_terraform_path()
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'validation_method' in content


def test_acm_certificate_uses_dns_validation():
    """Verify that ACM certificate uses DNS validation."""
    cert_file = _get_terraform_path()
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'DNS' in content


def test_route53_cert_validation_record_exists():
    """Verify that Route53 certificate validation record exists."""
    cert_file = _get_terraform_path()
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_route53_record" "cert_validation"' in content


def test_acm_certificate_validation_exists():
    """Verify that ACM certificate validation resource exists."""
    cert_file = _get_terraform_path()
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_acm_certificate_validation" "api"' in content


def test_route53_api_record_exists():
    """Verify that Route53 API record exists."""
    cert_file = _get_terraform_path()
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_route53_record" "api"' in content


def test_route53_api_record_is_alias():
    """Verify that Route53 API record is an alias."""
    cert_file = _get_terraform_path()
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'alias' in content


def test_route53_api_record_points_to_cloudfront():
    """Verify that Route53 API record points to CloudFront."""
    cert_file = _get_terraform_path()
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'cloudfront' in content.lower()
