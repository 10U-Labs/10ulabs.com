"""Tests for certificate and DNS Terraform configuration."""
import re


def test_certificate_dns_terraform_file_exists(website_src_path):
    """Test that certificate_dns.tf file exists."""
    assert (website_src_path / "certificate_dns.tf").exists()


def test_route53_zone_data_source_exists(certificate_dns_tf_content):
    """Test that Route53 zone data source exists."""
    assert 'data "aws_route53_zone" "parent"' in certificate_dns_tf_content


def test_acm_certificate_resource_exists(certificate_dns_tf_content):
    """Test that ACM certificate resource exists."""
    assert 'resource "aws_acm_certificate" "website"' in certificate_dns_tf_content


def test_acm_certificate_has_validation_method(certificate_dns_tf_content):
    """Test that ACM certificate has validation method."""
    pattern = r'validation_method\s*=\s*"DNS"'
    assert re.search(pattern, certificate_dns_tf_content), (
        "Expected validation_method = \"DNS\" in aws_acm_certificate resource"
    )


def test_acm_certificate_uses_dns_validation(certificate_dns_tf_content):
    """Test that ACM certificate uses DNS validation."""
    pattern = r'validation_method\s*=\s*"DNS"'
    assert re.search(pattern, certificate_dns_tf_content), (
        "Expected validation_method = \"DNS\" in aws_acm_certificate resource"
    )


def test_route53_cert_validation_record_exists(certificate_dns_tf_content):
    """Test that Route53 cert validation record exists."""
    assert 'resource "aws_route53_record" "cert_validation"' in certificate_dns_tf_content


def test_acm_certificate_validation_exists(certificate_dns_tf_content):
    """Test that ACM certificate validation resource exists."""
    assert 'resource "aws_acm_certificate_validation" "website"' in certificate_dns_tf_content


def test_acm_certificate_has_subject_alternative_names(certificate_dns_tf_content):
    """Test that ACM certificate has subject alternative names."""
    pattern = r'subject_alternative_names\s*=\s*\['
    assert re.search(pattern, certificate_dns_tf_content), (
        "Expected subject_alternative_names list in aws_acm_certificate resource"
    )


def test_route53_www_record_exists(certificate_dns_tf_content):
    """Test that Route53 www record exists."""
    assert 'resource "aws_route53_record" "www"' in certificate_dns_tf_content


def test_route53_www_record_is_alias(certificate_dns_tf_content):
    """Test that Route53 www record is an alias."""
    # Look for alias block within the www record context
    pattern = r'resource\s+"aws_route53_record"\s+"www"[^}]*\{[^}]*alias\s*\{'
    assert re.search(pattern, certificate_dns_tf_content, re.DOTALL), (
        "Expected alias block in aws_route53_record \"www\" resource"
    )


def test_route53_www_record_points_to_cloudfront(certificate_dns_tf_content):
    """Test that Route53 www record points to CloudFront."""
    pattern = r'name\s*=\s*aws_cloudfront_distribution\.\w+\.domain_name'
    assert re.search(pattern, certificate_dns_tf_content), (
        "Expected alias name referencing aws_cloudfront_distribution domain_name"
    )


def test_route53_www_ipv6_record_exists(certificate_dns_tf_content):
    """Test that Route53 www IPv6 record exists."""
    assert 'resource "aws_route53_record" "www_ipv6"' in certificate_dns_tf_content


def test_route53_www_ipv6_record_is_aaaa(certificate_dns_tf_content):
    """Test that Route53 www IPv6 record is AAAA type."""
    pattern = r'type\s*=\s*"AAAA"'
    assert re.search(pattern, certificate_dns_tf_content), (
        "Expected type = \"AAAA\" in aws_route53_record for IPv6"
    )


def test_route53_apex_record_exists(certificate_dns_tf_content):
    """Test that Route53 apex record exists."""
    assert 'resource "aws_route53_record" "apex"' in certificate_dns_tf_content


def test_route53_apex_ipv6_record_exists(certificate_dns_tf_content):
    """Test that Route53 apex IPv6 record exists."""
    assert 'resource "aws_route53_record" "apex_ipv6"' in certificate_dns_tf_content
