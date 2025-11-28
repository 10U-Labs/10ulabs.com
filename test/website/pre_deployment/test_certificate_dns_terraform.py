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


def test_acm_certificate_has_subject_alternative_names():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'subject_alternative_names' in content


def test_route53_www_record_exists():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_route53_record" "www"' in content


def test_route53_www_record_is_alias():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'alias' in content


def test_route53_www_record_points_to_cloudfront():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'cloudfront' in content.lower()


def test_route53_www_ipv6_record_exists():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_route53_record" "www_ipv6"' in content


def test_route53_www_ipv6_record_is_aaaa():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'type    = "AAAA"' in content


def test_route53_apex_record_exists():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_route53_record" "apex"' in content


def test_route53_apex_ipv6_record_exists():
    cert_file = Path(__file__).parent.parent.parent.parent / "src" / "website" / "certificate_dns.tf"
    with open(cert_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_route53_record" "apex_ipv6"' in content
