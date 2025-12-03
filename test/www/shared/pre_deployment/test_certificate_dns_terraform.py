def test_certificate_dns_terraform_file_exists(website_src_path):
    assert (website_src_path / "certificate_dns.tf").exists()


def test_route53_zone_data_source_exists(certificate_dns_tf_content):
    assert 'data "aws_route53_zone" "parent"' in certificate_dns_tf_content


def test_acm_certificate_resource_exists(certificate_dns_tf_content):
    assert 'resource "aws_acm_certificate" "website"' in certificate_dns_tf_content


def test_acm_certificate_has_validation_method(certificate_dns_tf_content):
    assert 'validation_method' in certificate_dns_tf_content


def test_acm_certificate_uses_dns_validation(certificate_dns_tf_content):
    assert 'DNS' in certificate_dns_tf_content


def test_route53_cert_validation_record_exists(certificate_dns_tf_content):
    assert 'resource "aws_route53_record" "cert_validation"' in certificate_dns_tf_content


def test_acm_certificate_validation_exists(certificate_dns_tf_content):
    assert 'resource "aws_acm_certificate_validation" "website"' in certificate_dns_tf_content


def test_acm_certificate_has_subject_alternative_names(certificate_dns_tf_content):
    assert 'subject_alternative_names' in certificate_dns_tf_content


def test_route53_www_record_exists(certificate_dns_tf_content):
    assert 'resource "aws_route53_record" "www"' in certificate_dns_tf_content


def test_route53_www_record_is_alias(certificate_dns_tf_content):
    assert 'alias' in certificate_dns_tf_content


def test_route53_www_record_points_to_cloudfront(certificate_dns_tf_content):
    assert 'cloudfront' in certificate_dns_tf_content.lower()


def test_route53_www_ipv6_record_exists(certificate_dns_tf_content):
    assert 'resource "aws_route53_record" "www_ipv6"' in certificate_dns_tf_content


def test_route53_www_ipv6_record_is_aaaa(certificate_dns_tf_content):
    assert 'type    = "AAAA"' in certificate_dns_tf_content


def test_route53_apex_record_exists(certificate_dns_tf_content):
    assert 'resource "aws_route53_record" "apex"' in certificate_dns_tf_content


def test_route53_apex_ipv6_record_exists(certificate_dns_tf_content):
    assert 'resource "aws_route53_record" "apex_ipv6"' in certificate_dns_tf_content
