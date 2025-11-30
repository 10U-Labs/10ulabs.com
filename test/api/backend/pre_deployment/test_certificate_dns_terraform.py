from pathlib import Path


def test_certificate_dns_terraform_file_exists():
    cert_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "certificate_dns.tf"
    assert cert_file.exists()


def test_route53_zone_data_source_exists():
    cert_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "aws_route53_zone" "parent"' in content


def test_acm_certificate_resource_exists():
    cert_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_acm_certificate" "api"' in content


def test_acm_certificate_has_validation_method():
    cert_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'validation_method' in content


def test_acm_certificate_uses_dns_validation():
    cert_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'DNS' in content


def test_route53_cert_validation_record_exists():
    cert_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_route53_record" "cert_validation"' in content


def test_acm_certificate_validation_exists():
    cert_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_acm_certificate_validation" "api"' in content


def test_route53_api_record_exists():
    cert_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_route53_record" "api"' in content


def test_route53_api_record_is_alias():
    cert_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'alias' in content


def test_route53_api_record_points_to_cloudfront():
    cert_file = Path(__file__).parent.parent.parent.parent.parent / "src" / "api" / "backend" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'cloudfront' in content.lower()
