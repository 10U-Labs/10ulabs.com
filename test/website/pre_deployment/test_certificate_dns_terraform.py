from pathlib import Path


def test_certificate_dns_terraform_file_exists():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    assert cert_file.exists()


def test_route53_zone_data_source_exists():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'data "aws_route53_zone" "parent"' in content


def test_acm_certificate_resource_exists():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_acm_certificate" "website"' in content


def test_acm_certificate_has_validation_method():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'validation_method' in content


def test_acm_certificate_uses_dns_validation():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'DNS' in content


def test_route53_cert_validation_record_exists():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_route53_record" "cert_validation"' in content


def test_acm_certificate_validation_exists():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_acm_certificate_validation" "website"' in content


def test_route53_website_record_exists():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_route53_record" "website"' in content


def test_route53_website_record_is_alias():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'alias' in content


def test_route53_website_record_points_to_cloudfront():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'cloudfront' in content.lower()


def test_route53_website_ipv6_record_exists():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_route53_record" "website_ipv6"' in content


def test_route53_website_ipv6_record_is_aaaa():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'type    = "AAAA"' in content
